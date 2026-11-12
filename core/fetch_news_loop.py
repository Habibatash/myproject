import time
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'د RSS خبرونو راټولول په ټاکلي واټن تکراروي؛ په جلا service/terminal کې یې وچلوئ.'
    def handle(self, *args, **opts):
        interval = max(1, settings.NEWS_FETCH_INTERVAL_MIN) * 60
        if not settings.NEWS_AUTOFETCH:
            self.stdout.write('NEWS_AUTOFETCH بند دی؛ worker نه چلېږي.')
            return
        self.stdout.write(f'RSS worker فعال شو؛ هر {interval//60} دقیقې.')
        while True:
            try: call_command('fetch_news_once')
            except Exception as exc: self.stderr.write(f'RSS worker error: {exc.__class__.__name__}: {exc}')
            time.sleep(interval)
