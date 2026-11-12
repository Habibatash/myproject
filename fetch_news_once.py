from django.core.management.base import BaseCommand
from core.news_ingest import fetch_all


class Command(BaseCommand):
    help = "Fetch public RSS/Atom news once"

    def handle(self, *args, **options):
        self.stdout.write(str(fetch_all()))
