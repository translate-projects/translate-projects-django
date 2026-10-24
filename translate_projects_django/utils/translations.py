import asyncio
import os

import polib
from django.conf import settings
from django.core.management import call_command
from rich.console import Console

from .api import Api
from .channels import listen_progress
from .hashing import generate_short_hash
from .po import generate_new_file_po
from .recreate_json import recreate_json

console = Console(log_time=True, log_path=False)


def generate_translations(self, target_lang, locale_dir):
    if not hasattr(self, "api_client"):
        self.api_client = Api()

    default_language = getattr(settings, "LANGUAGE_CODE", "")

    if not default_language:
        console.log("[red]❌ Error:[/] LANGUAGE_CODE is not set in settings.py")
        return None

    exclude_dirs = getattr(settings, "TRANSLATE_PROJECTS_EXCLUDE_DIRS", [])

    console.log(f"\n🚀 [bold green]Starting translation for language:[/] {target_lang}")

    # **Paso 1: Generate files .po**
    if target_lang == default_language:
        console.log("📂 [yellow]Step 1:[/] Generating .po file...")

    call_command("makemessages", locale=[target_lang], verbosity=0, ignore=exclude_dirs)

    # **Paso 2: read file .po**
    po_file_path = os.path.join(
        locale_dir, default_language, "LC_MESSAGES", "django.po"
    )
    po = polib.pofile(po_file_path)

    if target_lang == default_language:
        console.log(f"✅ [green].po file generated! ({len(po)} entries) [/]")

    # **Prepare translations**
    original_translations = {entry.msgid: entry.msgstr for entry in po}
    translations = {generate_short_hash(entry.msgid): entry.msgid for entry in po}

    # **Paso 3: Send translations API**
    if target_lang == default_language:
        console.log("📤 [yellow]Step 2:[/] Sending translations request...")
    if target_lang == default_language:
        response = self.api_client.sync_sources(
            translations,
            default_language,
            f"{default_language}-django.po",
        )

        if not response:
            return None

        task_id = response.get("task_id")
        if not task_id:
            console.log("❌ [red]Error:[/] No task_id received from API.")
            return None
        # **display progress bar**
        asyncio.run(listen_progress(task_id, default_language))
        return translations

    response = self.api_client.make_translations(
        default_language,
        target_lang,
        f"{default_language}-django.po",
    )
    if not response:
        return None

    task_id = response.get("task_id", None)

    if not task_id:
        console.log("❌ [red]Error:[/] No task_id received from API.")
        return None

    asyncio.run(listen_progress(task_id, target_lang))

    data_result_translations = self.api_client.get_translations(target_lang)

    if not data_result_translations:
        console.log("❌ [red]Error:[/] No translations received.")
        return None

    new_json_recreate = recreate_json(original_translations, data_result_translations)

    generate_new_file_po(po, target_lang, new_json_recreate, locale_dir)

    return True
