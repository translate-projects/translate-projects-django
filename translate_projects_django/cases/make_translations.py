from django.conf import settings
from django.core.management import call_command
from rich.console import Console

from translate_projects_django.utils.api import Api
from translate_projects_django.utils.translations import generate_translations

console = Console(log_time=True, log_path=False)


def make_translations(self, locale_param):
    languages = getattr(settings, "LANGUAGES", [])
    locale_dir = getattr(settings, "LOCALE_PATHS", [])[0]
    default_language = getattr(settings, "LANGUAGE_CODE", "")

    self.api_client = Api()

    console.log("🎯 [bold green]Start Generate Translations")

    # 🚀 Generar traducciones para el idioma predeterminado
    generate_translations(self, "es", locale_dir)

    if locale_param:
        # ⚠ Validar si el idioma proporcionado es válido
        if locale_param not in dict(languages):
            console.log(f"[red]❌ The language '{locale_param}' is not valid.[/]")
            console.log(
                f"[yellow]⚠ Available languages:[/] {', '.join([lang[0] for lang in languages])}"
            )
            console.log(
                "[blue]💡 You can add the language in settings.py under LANGUAGES=[...][/]"
            )
            return

        # ⚠ Advertir si el idioma es el mismo que el predeterminado
        if locale_param == default_language:
            console.log(
                f"[yellow]⚠ The language '{locale_param}' is not translated because it's the default language '{default_language}'.[/]"
            )
            return

        # 🚀 Traducir para el idioma específico
        console.log("\n🚀 [bold green]Translating for language:[/] {locale_param}")
        generate_translations(self, locale_param, locale_dir)
        console.log(
            f"\n🎉 [bold green]Translation for '{locale_param}' completed successfully ✅[/]\n"
        )

        # 🛠 Compilar mensajes
        console.log("\n🛠 [yellow]Compiling messages...[/]")
        call_command("compilemessages", verbosity=0)
        return

    # 🌍 Si no se proporciona un idioma específico, traducir todos los idiomas excepto el predeterminado
    for code, name in languages:
        if code != default_language:
            generate_translations(self, code, locale_dir)

    # 🛠 Compilar mensajes después de generar todas las traducciones
    console.log("\n🛠 [yellow]Compiling messages for all languages...[/]")

    call_command("compilemessages", verbosity=0)
    console.log(
        "\n🎉 [bold green]Translation generation for all languages completed successfully ✅[/]\n"
    )
