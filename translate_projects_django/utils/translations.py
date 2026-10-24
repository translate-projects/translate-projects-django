import copy
import json
import os
import re
import time

import polib
from django.core.management import call_command
from django.utils.translation import to_locale
from rich.console import Console

from .channels import wait_task
from .hashing import generate_short_hash

console = Console(log_time=True, log_path=False)

# Texts the backend never stores (helpers/ignore_list.py), so they never come back translated
IGNORED = {"", ".", ",", ":", ";", "..."}
PLACEHOLDER = re.compile(r"%\([^)]+\)[a-z]|%[a-z]|\{[\w.]*\}")
CACHE_FILE = ".translate-projects.json"


def to_api_lang(code):
    """Django "pt-br" / "zh-hans" → backend "pt-BR" / "zh-Hans"."""
    lang, _, region = code.partition("-")
    if not region:
        return lang
    return f"{lang}-{region.upper() if len(region) == 2 else region.title()}"


def po_path(locale_dir, lang):
    return os.path.join(locale_dir, to_locale(lang), "LC_MESSAGES", "django.po")


def route_file(default_language):
    return f"{default_language}-django.po"


def extract_sources(default_language, locale_dir, exclude_dirs):
    """Runs makemessages for the source language and returns (po, {hash: msgid})."""
    call_command(
        "makemessages",
        locale=[to_locale(default_language)],
        verbosity=0,
        ignore=exclude_dirs,
    )
    po = polib.pofile(po_path(locale_dir, default_language))
    # shortcut: plural entries (msgid_plural) are left untranslated; handle them when a project uses ngettext
    sources = {
        generate_short_hash(e.msgid): e.msgid
        for e in po
        if not e.obsolete and not e.msgid_plural and e.msgid not in IGNORED
    }
    return po, sources


def cache_hash(sources):
    return generate_short_hash(json.dumps(sorted(sources)))


def sync_sources(api, sources, default_language, version):
    """Uploads the source texts unless the backend already has this exact version."""
    file_hash = generate_short_hash(route_file(default_language))
    changed = api.validate_changes({file_hash: version})
    if changed is not None and file_hash not in changed:
        console.log("✅ [green]Sources unchanged, upload skipped[/]")
        return True

    response = api.sync_sources(
        sources, to_api_lang(default_language), route_file(default_language), version
    )
    if not response or not response.get("task_id"):
        console.log("❌ [red]Error:[/] Sources upload failed.")
        return False
    wait_task(response["task_id"])
    return True


def placeholders_ok(source, translation):
    return sorted(PLACEHOLDER.findall(source)) == sorted(
        PLACEHOLDER.findall(translation)
    )


def write_po(po, lang, translations, locale_dir):
    """Writes a copy of the source .po with the msgstr filled in. Returns (filled, rejected)."""
    new_po = copy.deepcopy(po)
    new_po.metadata["Language"] = to_locale(lang)
    new_po.metadata_is_fuzzy = False
    filled, rejected = 0, []
    for entry in new_po:
        entry.msgstr = ""
        if "fuzzy" in entry.flags:
            entry.flags.remove("fuzzy")
        translation = translations.get(entry.msgid)
        if not translation:
            continue
        # A broken placeholder makes compilemessages fail, so keep the source text instead
        if not placeholders_ok(entry.msgid, translation):
            rejected.append(entry.msgid)
            continue
        entry.msgstr = translation
        filled += 1
    path = po_path(locale_dir, lang)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new_po.save(path)
    return filled, rejected


def load_cache(locale_dir):
    try:
        with open(os.path.join(locale_dir, CACHE_FILE)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_cache(locale_dir, cache):
    with open(os.path.join(locale_dir, CACHE_FILE), "w") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def translate_language(api, po, sources, lang, default_language, locale_dir, on_progress):
    """Asks the backend to translate `lang`, downloads the result and writes its .po."""
    timings = {}
    started = time.monotonic()
    response = api.make_translations(
        to_api_lang(default_language), to_api_lang(lang), route_file(default_language)
    )
    if not response or not response.get("task_id"):
        console.log(f"❌ [red]Error:[/] Could not start the translation of {lang}.")
        return None
    wait_task(response["task_id"], on_progress)
    timings["translate"] = time.monotonic() - started

    started = time.monotonic()
    by_hash = api.get_translations(to_api_lang(lang))
    timings["download"] = time.monotonic() - started
    if by_hash is None:
        console.log(f"❌ [red]Error:[/] No translations received for {lang}.")
        return None

    started = time.monotonic()
    translations = {msgid: by_hash[h] for h, msgid in sources.items() if h in by_hash}
    filled, rejected = write_po(po, lang, translations, locale_dir)
    timings["write"] = time.monotonic() - started

    missing = len(sources) - len(translations)
    if missing:
        console.log(
            f"⚠ [yellow]{lang}: {missing} texts without translation. "
            "Check that the project has an AI model and API key configured.[/]"
        )
    for msgid in rejected:
        console.log(f"⚠ [yellow]{lang}: placeholders changed, kept source:[/] {msgid!r}")
    return {
        "lang": lang,
        "filled": filled,
        "missing": missing,
        "rejected": len(rejected),
        "timings": timings,
    }
