from django.core.management import call_command
from django.conf import settings
from translate_projects_django.manage_translations import generate_translations
import os
from translate_projects_django.api_utils import Api

def make_translations(self,locale_param):    

    languages = getattr(settings, 'LANGUAGES', [])
    locale_dir = getattr(settings, 'LOCALE_PATHS', [])[0]
    default_language = getattr(settings, 'LANGUAGE_CODE', '')

    self.api_client = Api()
    # Generate translations for the default language ('es' in this case)
    generate_translations(self, 'es', locale_dir)
    
    if locale_param:
        # Check if the provided locale is valid
        if locale_param not in dict(languages):
            self.stdout.write(self.style.ERROR(f"The language '{locale_param}' is not valid."))
            self.stdout.write(self.style.ERROR(f"Available languages: {', '.join([lang[0] for lang in languages])}"))
            self.stdout.write(self.style.ERROR(f"You can add the language in the settings.py file under LANGUAGES=[...]"))
            return

        # Warn if the locale is the same as the default language
        if locale_param == default_language:
            self.stdout.write(self.style.WARNING(f"The language '{locale_param}' is not translated, as the default language '{default_language}' has already been translated."))
            return

        # Translate for the specific locale
        self.stdout.write(self.style.SUCCESS(f"\n🚀 Translating for language: {locale_param}"))
        generate_translations(self, locale_param, locale_dir)
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Translation generation for '{locale_param}' completed successfully ✅\n"))

        # Compile messages
        self.stdout.write(self.style.WARNING(f"\n🛠 Compiling messages..."))
        call_command('compilemessages',verbosity=0)
        return

    # If no specific locale is passed, generate translations for all languages except the default language
    for code, name in languages:
        if code != default_language:
            generate_translations(self, code, locale_dir)

    # Compile messages after translations are generated for all languages
    self.stdout.write(self.style.WARNING(f"\n🛠 Compiling messages for all languages..."))
    call_command('compilemessages',verbosity=0)
    self.stdout.write(self.style.SUCCESS(f"\n🎉 Translation generation for all languages completed successfully ✅\n"))