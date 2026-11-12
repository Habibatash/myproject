import json, re
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import ExternalNews


def clean_html(value):
    return re.sub(r'<[^>]+>', ' ', value or '').replace('&amp;','&').replace('&nbsp;',' ').strip()[:5000]

def parse_date(value):
    if not value: return None
    try:
        d = parsedate_to_datetime(value)
    except Exception:
        try: d = datetime.fromisoformat(value.replace('Z','+00:00'))
        except Exception: return None
    if timezone.is_naive(d): d = timezone.make_aware(d, dt_timezone.utc)
    return d

def local(tag): return tag.rsplit('}',1)[-1].lower()

def children_map(el):
    return {local(c.tag): (c.text or '').strip() for c in el}

class Command(BaseCommand):
    help = 'له NEWS_FEEDS_JSON څخه RSS/Atom خبرونه راټولوي.'
    def handle(self, *args, **opts):
        try: feeds = json.loads(settings.NEWS_FEEDS_JSON or '[]')
        except json.JSONDecodeError as exc: raise CommandError(f'NEWS_FEEDS_JSON ناسم JSON دی: {exc}')
        if not isinstance(feeds, list): raise CommandError('NEWS_FEEDS_JSON باید د سرچینو لېست وي.')
        saved = 0
        for feed in feeds:
            url = feed.get('url',''); source = feed.get('name') or url
            if not url.startswith('https://'):
                self.stderr.write(f'ناامنه یا ناسمه سرچینه پرېښودل شوه: {source}'); continue
            try:
                req = Request(url, headers={'User-Agent':'AgencyUnifiedSystem/1.0 (+RSS reader)'})
                with urlopen(req, timeout=20) as resp: root = ET.fromstring(resp.read())
            except (URLError, HTTPError, TimeoutError, ET.ParseError) as exc:
                self.stderr.write(f'{source}: {exc.__class__.__name__}'); continue
            items = [el for el in root.iter() if local(el.tag) in {'item','entry'}]
            for el in items:
                data = children_map(el)
                title = data.get('title','').strip()
                link = data.get('link','').strip()
                if not link:
                    for c in el:
                        if local(c.tag) == 'link':
                            link = c.attrib.get('href') or (c.text or '').strip(); break
                summary = clean_html(data.get('description') or data.get('summary') or data.get('content',''))
                if title and link.startswith('https://'):
                    _, created = ExternalNews.objects.get_or_create(url=link, defaults={
                        'title':title[:400], 'summary':summary, 'source':source[:180],
                        'published_at':parse_date(data.get('pubdate') or data.get('published') or data.get('updated')),
                    })
                    saved += int(created)
        cutoff = timezone.now() - timedelta(days=settings.NEWS_KEEP_DAYS)
        ExternalNews.objects.filter(fetched_at__lt=cutoff, is_featured=False).delete()
        self.stdout.write(self.style.SUCCESS(f'نوي خبرونه ثبت شول: {saved}'))
