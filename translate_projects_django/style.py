import sys
from django.core.management.base import BaseCommand

class StyledMessages(BaseCommand):
    def __init__(self):
        super().__init__()  

    def error(self, message):
        sys.stderr.write(self.style.ERROR(f"{message}\n"))

    def success(self, message):
        sys.stdout.write(self.style.SUCCESS(f"{message}\n"))

    def warning(self, message):
        sys.stdout.write(self.style.WARNING(f"{message}\n")) 
