import time
from django.conf import settings
from django.core.management.base import BaseCommand
from core.news_ingest import fetch_all


class Command(BaseCommand):
    help = "Continuously fetch public RSS/Atom news; supervise this process in production"

    def handle(self, *args, **options):
        minutes = max(5, int(getattr(settings, "NEWS_FETCH_INTERVAL_MIN", 15)))
        self.stdout.write(self.style.SUCCESS(f"RSS collector running every {minutes} minutes"))
        while True:
            try:
                self.stdout.write(str(fetch_all()))
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"Collector iteration failed: {exc}")
            time.sleep(minutes * 60)
