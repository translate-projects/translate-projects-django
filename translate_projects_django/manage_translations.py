from django.core.management import call_command
from .translation_utils import generate_new_file_po
from .api_utils import get_translations_from_api
from .hash_utils import generate_short_hash
from django.conf import settings
import polib
import os

def make_recreate_json(original_translations, data_result_translations):
    recreate_json = {}
    for key, value in original_translations.items():
        simple_hash = generate_short_hash(key)
        
        if simple_hash in data_result_translations.keys():
            recreate_json[key] = data_result_translations[simple_hash]
            continue
    return recreate_json

def generate_translations(self, target_lang, locale_dir):
    default_language = settings.LANGUAGE_CODE

    # Start
    self.stdout.write(self.style.SUCCESS(f"\n🚀 Starting translation generation for language: {target_lang}"))

    # Step 1: Generate files .po
    self.stdout.write(self.style.WARNING(f"  Step 1: Generating .po file for '{target_lang}'..."))
    
    call_command('makemessages', locale=[target_lang], verbosity=0)
    
    self.stdout.write(self.style.SUCCESS(f"    ✔ .po file generated for '{target_lang}'"))

    # Step 2: Read File .po
    po_file_path = os.path.join(locale_dir, default_language, 'LC_MESSAGES', 'django.po')
    
    po = polib.pofile(po_file_path)
    self.stdout.write(self.style.SUCCESS(f"    ✔ .po file read successfully (entries: {len(po)}))"))
    
    original_translations = {entry.msgid: entry.msgstr for entry in po}
    
    translations = {
        generate_short_hash(entry.msgid): entry.msgid
        for entry in po
    }
    
    self.stdout.write(self.style.SUCCESS(f"    ✔ Hashed translations generated (total: {len(translations)}))"))

    # Step 2: Get translations from API
    self.stdout.write(self.style.WARNING(f"  Step 2: get translations for '{target_lang}'..."))
    data_result_translations = get_translations_from_api(translations, default_language, target_lang, f"{default_language}-django.po")
    self.stdout.write(self.style.SUCCESS(f"    ✔ Translations get (received: {len(data_result_translations)}))"))

    # Step 5: Recreate translations
    recreate_json = make_recreate_json(original_translations, data_result_translations)

    # Paso 3: Generate new translations file
    self.stdout.write(self.style.WARNING(f"  Step 3: Generating new translations file for '{target_lang}'..."))
    generate_new_file_po(po, target_lang, recreate_json, locale_dir)
    self.stdout.write(self.style.SUCCESS(f"    ✔ New .po file generated for '{target_lang}'"))

    # Finish
    self.stdout.write(self.style.SUCCESS(f"\n🎉 Successfully completed translation generation for '{target_lang}' ✅\n"))
