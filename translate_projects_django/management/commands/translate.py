from django.core.management.base import BaseCommand

from translate_projects_django.cases.make_translations import make_translations


class Command(BaseCommand):
    help = "Translate the project for a specific language or all languages."

    def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            type=str,
            help='Specific language to translate, e.g., "ko" for Korean.',
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Translate every language even if its .po is up to date "
            "(pulls edits made in the dashboard).",
        )

    def handle(self, *args, **kwargs):
        make_translations(self, kwargs.get("locale"), force=kwargs.get("force"))
