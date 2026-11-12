from django.core.management.base import BaseCommand, CommandError
from core.newsfeeds import fetch_all


class Command(BaseCommand):
    help = 'د افغانستان، پاکستان، ایران او امریکا اړوند خبرونه له RSS سرچینو راټولوي او په برخو ویشي.'

    def handle(self, *args, **opts):
        try:
            saved = fetch_all(log=lambda m: self.stderr.write(m))
        except ValueError as exc:
            raise CommandError(f'NEWS_FEEDS_JSON ناسم دی: {exc}')
        self.stdout.write(self.style.SUCCESS(f'نوي خبرونه ثبت شول: {saved}'))
