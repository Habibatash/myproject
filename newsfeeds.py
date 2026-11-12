"""Automatic collection and classification of external news (Afghanistan, Pakistan, Iran, USA).

Only public RSS/Atom feeds are read (news sites and Google News search feeds). Social networks do not
offer free public feeds, so they are not scraped; add any public RSS URL through NEWS_FEEDS_JSON.
"""
import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from django.conf import settings
from django.utils import timezone

from .models import ExternalNews

GN = 'https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}'


def _gn(q, lang='en'):
    q = q.replace(' ', '+')
    if lang == 'fa':
        return GN.format(q=q, hl='fa', gl='AF', ceid='AF:fa')
    return GN.format(q=q, hl='en-US', gl='US', ceid='US:en')


# region is the declared region of a feed; None means "detect from the text".
DEFAULT_FEEDS = [
    {'name': 'Google News · Afghanistan', 'url': _gn('Afghanistan'), 'region': 'afghanistan'},
    {'name': 'Google News · افغانستان', 'url': _gn('افغانستان', 'fa'), 'region': 'afghanistan'},
    {'name': 'Google News · Afghanistan security', 'url': _gn('Afghanistan security'), 'region': 'afghanistan'},
    {'name': 'Google News · Afghanistan economy', 'url': _gn('Afghanistan economy'), 'region': 'afghanistan'},
    {'name': 'Google News · Afghanistan technology', 'url': _gn('Afghanistan technology'), 'region': 'afghanistan'},
    {'name': 'Google News · Pakistan', 'url': _gn('Pakistan'), 'region': 'pakistan'},
    {'name': 'Google News · Iran', 'url': _gn('Iran'), 'region': 'iran'},
    {'name': 'Google News · United States', 'url': _gn('United States'), 'region': 'usa'},
    {'name': 'BBC Pashto', 'url': 'https://feeds.bbci.co.uk/pashto/rss.xml', 'region': None},
    {'name': 'BBC Persian', 'url': 'https://feeds.bbci.co.uk/persian/rss.xml', 'region': None},
    {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'region': None},
]

REGION_WORDS = {
    'afghanistan': ['afghan', 'kabul', 'taliban', 'kandahar', 'herat', 'mazar', 'jalalabad', 'kunduz', 'panjshir',
                    'افغان', 'کابل', 'طالبان', 'کندهار', 'هرات', 'ننګرهار', 'پنجشیر', 'امارت اسلامي', 'امارت اسلامی'],
    'pakistan': ['pakistan', 'islamabad', 'karachi', 'lahore', 'peshawar', 'quetta', 'پاکستان', 'اسلام آباد', 'اسلام‌آباد', 'کراچي', 'کراچی', 'پېښور', 'پشاور'],
    'iran': ['iran', 'tehran', 'تهران', 'ایران', 'ايران', 'اېران'],
    'usa': ['united states', 'u.s.', 'american', 'washington', 'white house', 'pentagon', 'امریکا', 'آمریکا', 'امريكا', 'واشنګټن', 'واشنگتن', 'سپینه ماڼۍ', 'کاخ سفید'],
}

CATEGORY_WORDS = [
    ('security', ['attack', 'killed', 'blast', 'explosion', 'military', 'border', 'clash', 'security', 'army', 'terror', 'isis', 'drone', 'airstrike', 'war',
                  'حمله', 'انفجار', 'امنیت', 'امنیتي', 'نظامي', 'نظامی', 'مرز', 'پولیس', 'ترهګر', 'تروریست', 'جګړه', 'جنگ']),
    ('economic', ['economy', 'trade', 'bank', 'price', 'market', 'dollar', 'afghani', 'currency', 'export', 'import', 'inflation', 'aid', 'gdp', 'budget', 'oil', 'gold',
                  'اقتصاد', 'تجارت', 'بانک', 'بازار', 'قیمت', 'ډالر', 'دالر', 'افغاني', 'صادرات', 'واردات', 'بودجه']),
    ('technology', ['technology', 'tech', 'internet', 'cyber', 'ai ', 'artificial intelligence', 'software', 'telecom', 'mobile', 'satellite', 'starlink',
                    'ټکنالوژي', 'تکنالوژی', 'تکنولوژی', 'انټرنېټ', 'اینترنت', 'سایبري', 'مخابرات', 'هوش مصنوعی']),
    ('health', ['health', 'hospital', 'disease', 'vaccine', 'polio', 'cholera', 'covid', 'روغتیا', 'صحت', 'روغتون', 'ناروغي', 'واکسین']),
    ('sports', ['cricket', 'football', 'soccer', 'olympic', 'match', 'tournament', 'world cup', 'کرکټ', 'کریکت', 'فوتبال', 'ورزش', 'لوبه', 'المپیک']),
    ('political', ['government', 'minister', 'talks', 'diplomat', 'sanction', 'election', 'president', 'un ', 'united nations', 'policy', 'embassy', 'recognition',
                   'حکومت', 'وزیر', 'مذاکره', 'ډیپلومات', 'تحریم', 'انتخابات', 'ولسمشر', 'سفارت', 'سیاسي', 'سیاسی', 'ملګري ملتونه', 'ملل متحد']),
]
BREAKING_WORDS = ['breaking', 'urgent', 'just in', 'developing', 'عاجل', 'فوري', 'فوری', 'لومړنی خبر', 'خبر عاجل']


def _local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def clean_html(value):
    return re.sub(r'<[^>]+>', ' ', value or '').replace('&amp;', '&').replace('&nbsp;', ' ').strip()[:5000]


def parse_date(value):
    if not value:
        return None
    try:
        d = parsedate_to_datetime(value)
    except Exception:
        try:
            d = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except Exception:
            return None
    if d is None:
        return None
    if timezone.is_naive(d):
        d = timezone.make_aware(d, dt_timezone.utc)
    return d


def detect_regions(text, declared=None):
    low = (text or '').casefold()
    found = {r for r, words in REGION_WORDS.items() if any(w in low for w in words)}
    if declared:
        found.add(declared)
    return found


def classify(title, summary, published_at):
    low = f'{title} {summary}'.casefold()
    breaking = any(w in low for w in BREAKING_WORDS) or bool(published_at and timezone.now() - published_at < timedelta(hours=2))
    head = f'{title} '.casefold()
    for cat, words in CATEGORY_WORDS:
        if any(w in head for w in words):
            return cat, breaking
    for cat, words in CATEGORY_WORDS:
        if any(w in low for w in words):
            return cat, breaking
    return 'other', breaking


def load_feeds():
    raw = (getattr(settings, 'NEWS_FEEDS_JSON', '') or '').strip()
    feeds = []
    if raw:
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError('NEWS_FEEDS_JSON must be a JSON list')
        feeds.extend(f for f in data if isinstance(f, dict))
    if getattr(settings, 'NEWS_USE_DEFAULT_FEEDS', True):
        feeds.extend(DEFAULT_FEEDS)
    return feeds


def fetch_all(log=None):
    """Download every feed once; return the number of new items. Never raises for a single bad feed."""
    log = log or (lambda msg: None)
    saved = 0
    for feed in load_feeds():
        url = feed.get('url', '')
        source = feed.get('name') or url
        if not url.startswith('https://'):
            log(f'ناامنه سرچینه پرېښودل شوه: {source}')
            continue
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (AgencyUnifiedSystem RSS reader)'})
            with urlopen(req, timeout=20) as resp:
                root = ET.fromstring(resp.read())
        except (URLError, HTTPError, TimeoutError, ET.ParseError, OSError) as exc:
            log(f'{source}: {exc.__class__.__name__}')
            continue
        declared = feed.get('region')
        for el in [e for e in root.iter() if _local(e.tag) in {'item', 'entry'}][:60]:
            data = {_local(c.tag): (c.text or '').strip() for c in el}
            title = clean_html(data.get('title', ''))[:400]
            link = data.get('link', '')
            if not link:
                for c in el:
                    if _local(c.tag) == 'link':
                        link = c.attrib.get('href') or (c.text or '').strip()
                        break
            if not title or not link.startswith('https://'):
                continue
            summary = clean_html(data.get('description') or data.get('summary') or data.get('content', ''))
            published = parse_date(data.get('pubdate') or data.get('published') or data.get('updated'))
            regions = detect_regions(f'{title} {summary}', declared)
            if not regions:
                continue  # only keep news that actually talks about one of the tracked countries
            category, breaking = classify(title, summary, published)
            _, created = ExternalNews.objects.get_or_create(url=link, defaults={
                'title': title, 'summary': summary, 'source': (data.get('source') or source)[:180],
                'published_at': published, 'regions': ',' + ','.join(sorted(regions)) + ',',
                'category': category, 'is_breaking': breaking,
            })
            saved += int(created)
    cutoff = timezone.now() - timedelta(days=settings.NEWS_KEEP_DAYS)
    ExternalNews.objects.filter(fetched_at__lt=cutoff, is_featured=False).delete()
    return saved


_lock = threading.Lock()
_state = {'last': 0.0, 'running': False}


def refresh_in_background(force=False):
    """Start a background refresh when the newest data is older than the interval.

    This keeps the news section alive even if the separate `fetch_news_loop` worker is not running.
    """
    interval = max(1, settings.NEWS_FETCH_INTERVAL_MIN) * 60
    with _lock:
        if _state['running'] or (not force and time.time() - _state['last'] < interval):
            return False
        _state['running'] = True
        _state['last'] = time.time()

    def run():
        try:
            fetch_all()
        except Exception:
            pass
        finally:
            _state['running'] = False

    threading.Thread(target=run, daemon=True, name='news-refresh').start()
    return True
