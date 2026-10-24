import os
import time
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management import call_command
from rich.console import Console
from rich.progress import Progress

from translate_projects_django.utils.api import Api
from translate_projects_django.utils.translations import (
    cache_hash,
    extract_sources,
    load_cache,
    po_path,
    save_cache,
    sync_sources,
    translate_language,
)

console = Console(log_time=True, log_path=False)

PARALLEL_LANGUAGES = 3


def make_translations(self, locale_param, force=False):
    languages = dict(getattr(settings, "LANGUAGES", []))
    locale_paths = getattr(settings, "LOCALE_PATHS", [])
    default_language = getattr(settings, "LANGUAGE_CODE", "")
    exclude_dirs = getattr(settings, "TRANSLATE_PROJECTS_EXCLUDE_DIRS", [])

    if not getattr(settings, "TRANSLATE_PROJECTS_API_KEY", None):
        console.log("[red]❌ TRANSLATE_PROJECTS_API_KEY is not set in settings.py[/]")
        return
    if not default_language or not locale_paths:
        console.log("[red]❌ LANGUAGE_CODE and LOCALE_PATHS must be set in settings.py[/]")
        return
    locale_dir = str(locale_paths[0])

    if locale_param:
        if locale_param not in languages:
            console.log(f"[red]❌ The language '{locale_param}' is not valid.[/]")
            console.log(f"[yellow]⚠ Available languages:[/] {', '.join(languages)}")
            console.log("[blue]💡 Add it in settings.py under LANGUAGES=[...][/]")
            return
        if locale_param == default_language:
            console.log(
                f"[yellow]⚠ '{locale_param}' is the default language, nothing to translate.[/]"
            )
            return
        targets = [locale_param]
    else:
        targets = [code for code in languages if code != default_language]

    api = Api()
    run_started = time.monotonic()
    console.log("🎯 [bold green]Start Generate Translations")

    started = time.monotonic()
    po, sources = extract_sources(default_language, locale_dir, exclude_dirs)
    extract_time = time.monotonic() - started
    console.log(f"📂 {len(sources)} texts found in {default_language}")

    started = time.monotonic()
    version = cache_hash(sources)
    if not sync_sources(api, sources, default_language, version):
        return
    upload_time = time.monotonic() - started

    cache = load_cache(locale_dir)
    pending = [
        lang
        for lang in targets
        if force
        or cache.get(lang) != version
        or not os.path.exists(po_path(locale_dir, lang))
    ]
    for lang in set(targets) - set(pending):
        console.log(f"✅ [green]{lang} is up to date, skipped[/]")

    results = []
    if pending:
        with Progress(console=console) as progress, ThreadPoolExecutor(
            PARALLEL_LANGUAGES
        ) as pool:

            def run(lang):
                bar = progress.add_task(f"📝 Translating ({lang})", total=100)
                return translate_language(
                    api, po, sources, lang, default_language, locale_dir,
                    lambda p: progress.update(bar, completed=p),
                )

            results = [r for r in pool.map(run, pending) if r]

    for result in results:
        if result["missing"]:
            cache.pop(result["lang"], None)
        else:
            cache[result["lang"]] = version
    if results:
        save_cache(locale_dir, cache)

    started = time.monotonic()
    call_command("compilemessages", verbosity=0, ignore=exclude_dirs)
    compile_time = time.monotonic() - started

    console.log(
        f"⏱ extract {extract_time:.1f}s · upload {upload_time:.1f}s · "
        f"compile {compile_time:.1f}s · total {time.monotonic() - run_started:.1f}s · "
        f"{api.requests_made} HTTP requests"
    )
    for r in results:
        t = r["timings"]
        console.log(
            f"   {r['lang']}: {r['filled']} filled, {r['missing']} missing, "
            f"{r['rejected']} rejected · translate {t['translate']:.1f}s · "
            f"download {t['download']:.1f}s · write {t['write']:.1f}s"
        )
    console.log("🎉 [bold green]Translations completed ✅[/]")
