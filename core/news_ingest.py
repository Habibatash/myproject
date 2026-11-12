"""RSS/Atom news collector. Uses only public feeds configured by the operator."""
import hashlib
import html
import json
import logging
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime

from django.conf import settings
from django.utils import timezone

from .news_models import ExternalNews

log = logging.getLogger("core")

DEFAULT_FEEDS = [
    {"country": "afghanistan", "source": "TOLOnews", "url": "https://www.tolonews.com/rss.xml", "language": "ps"},
    {"country": "afghanistan", "source": "RFE/RL Afghanistan", "url": "https://www.rferl.org/api/zvoi_l-vomx-tpeukmy", "language": "ps"},
    {"country": "iran", "source": "RFE/RL Iran", "url": "https://www.rferl.org/api/z-oiil-vomx-tpergmp", "language": "fa"},
    {"country": "pakistan", "source": "RFE/RL Pakistan", "url": "https://www.rferl.org/api/zgrgml-vomx-tpe-t-_", "language": "en"},
    {"country": "world", "source": "RFE/RL World", "url": "https://www.rferl.org/api/zbqiml-vomx-tpeqkmy", "language": "en"},
    {"country": "world", "source": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "language": "en"},
    {"country": "usa", "source": "BBC US & Canada", "url": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml", "language": "en"},
]

WORDS = {
    "urgent": ["عاجل", "بیړنی", "فوري", "breaking", "urgent", "emergency", "هشدار فوری"],
    "political": ["سیاست", "سیاسي", "حکومت", "پارلمان", "انتخابات", "president", "government", "election", "diplomat", "پارلماني"],
    "security": ["امنیت", "امنیتي", "برید", "چاودنه", "وسله وال", "attack", "security", "military", "explosion", "terror"],
    "economy": ["اقتصاد", "اقتصادي", "بازار", "بانک", "بیه", "تورم", "اقتصاد", "economic", "market", "inflation", "trade"],
    "technology": ["ټکنالوژي", "تکنالوژي", "مصنوعي ځیرکتیا", "انټرنېټ", "technology", "artificial intelligence", "cyber", "digital"],
    "society": ["ټولنه", "ټولنیز", "کډوال", "بشري حقونه", "society", "social", "migration", "human rights"],
    "education": ["ښوونه", "تعلیم", "پوهنتون", "ښوونځی", "education", "school", "university"],
    "health": ["روغتیا", "روغتیايي", "درمل", "health", "hospital", "vaccine"],
    "sports": ["لوبې", "کرکټ", "فوټبال", "sports", "cricket", "football"],
}
COUNTRY_WORDS = {
    "afghanistan": ["افغانستان", "کابل", "هرات", "کندهار", "بلخ", "afghanistan", "kabul", "taliban"],
    "pakistan": ["پاکستان", "اسلام اباد", "کراچۍ", "لاهور", "pakistan", "islamabad"],
    "iran": ["ایران", "تهران", "مشهد", "iran", "tehran"],
    "usa": ["امریکا", "متحده ایالات", "واشنګټن", "امریکايي", "united states", "washington", "u.s.", "usa"],
}


def _feeds():
    raw = getattr(settings, "NEWS_FEEDS_JSON", "")
    if raw:
        try:
            rows = json.loads(raw)
            if isinstance(rows, list):
                return [x for x in rows if isinstance(x, dict) and x.get("url") and x.get("country") in {"afghanistan", "world", "pakistan", "iran", "usa"}]
        except (ValueError, TypeError):
            log.exception("NEWS_FEEDS_JSON is invalid; using built-in feeds")
    return DEFAULT_FEEDS


def _text(node, *names):
    for name in names:
        found = node.find(name)
        if found is None:
            found = node.find("{*}" + name)
        if found is not None:
            if name == "link":
                href = found.attrib.get("href")
                if href:
                    return href.strip()
            val = " ".join(found.itertext()).strip()
            if val:
                return val
    return ""


def _published(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_timezone.utc)
    return dt.astimezone(dt_timezone.utc)


def _clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _category(title, summary):
    text = (title + " " + summary).lower()
    for key in ("urgent", "security", "political", "economy", "technology", "society", "education", "health", "sports"):
        if any(word.lower() in text for word in WORDS[key]):
            return key
    return "other"


def _country(title, summary, feed_country):
    if feed_country in ("afghanistan", "pakistan", "iran", "usa"):
        return feed_country
    text = (title + " " + summary).lower()
    hits = [(sum(1 for w in terms if w.lower() in text), country) for country, terms in COUNTRY_WORDS.items()]
    hits.sort(reverse=True)
    if hits and hits[0][0] > 0:
        return hits[0][1]
    return feed_country if feed_country in ("afghanistan", "world", "pakistan", "iran", "usa") else "world"


def fetch_all():
    if not getattr(settings, "NEWS_AUTOFETCH", True):
        return {"disabled": True, "created": 0, "updated": 0, "errors": 0}
    created = updated = errors = 0
    headers = {"User-Agent": "AgencyNewsCollector/1.0 (+public RSS reader)", "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"}
    for feed in _feeds():
        url = feed.get("url", "")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=18) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError("Feed exceeds 4 MB limit")
            root = ET.fromstring(raw)
            entries = root.findall(".//item") or root.findall(".//{*}entry")
            for node in entries[:200]:
                title = _clean(_text(node, "title"))[:500]
                link = _text(node, "link") or _text(node, "guid", "id")
                summary = _clean(_text(node, "description", "summary", "content"))[:6000]
                published = _published(_text(node, "pubDate", "published", "updated", "date"))
                if not title or not link or not link.startswith(("http://", "https://")):
                    continue
                digest = hashlib.sha256((title + "\n" + link).encode("utf-8")).hexdigest()
                _, was_created = ExternalNews.objects.update_or_create(
                    url=link,
                    defaults={"title": title, "summary": summary, "source": (feed.get("source") or "RSS")[:200],
                              "country": _country(title, summary, feed.get("country", "world")),
                              "category": _category(title, summary), "language": (feed.get("language") or "")[:20],
                              "published_at": published, "content_hash": digest},
                )
                created += int(was_created)
                updated += int(not was_created)
        except Exception as exc:  # keep other sources running if one feed fails
            errors += 1
            log.warning("RSS fetch failed (%s): %s", url, exc)
    days = max(1, int(getattr(settings, "NEWS_KEEP_DAYS", 14)))
    ExternalNews.objects.filter(fetched_at__lt=timezone.now() - timedelta(days=days)).delete()
    return {"created": created, "updated": updated, "errors": errors}
