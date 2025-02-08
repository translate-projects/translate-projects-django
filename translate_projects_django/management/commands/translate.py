from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
from django.core.management import call_command
import polib
import json
import os
import requests
from translate_projects_django.cases.make_translations import make_translations

class Command(BaseCommand):
    help = "Translate the project for a specific language or all languages."

    def add_arguments(self, parser):
        # Add an optional argument for the locale
        parser.add_argument(
            '--locale', 
            type=str, 
            help='Specific language to translate, e.g., "ko" for Korean.'
        )
        # get translations api
        parser.add_argument(
            '--get',
            action='store_true',
            help='Get translations from API',
            default=False
        )

    def handle(self, *args, **kwargs):
        # Get the locale argument
        locale_param = kwargs.get('locale')

        # Get the get argument
        get_translations = kwargs.get('get')

        if get_translations:
            #logic for get translations
            return

        if not get_translations:
            make_translations(self, locale_param)
            return