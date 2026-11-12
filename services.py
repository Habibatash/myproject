import re
from django.utils import timezone
from .models import Notification, AuditEvent, User


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')


def audit(request, action, summary, obj=None, details=None):
    AuditEvent.objects.create(
        actor=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__ if obj else '',
        object_id=str(obj.pk) if obj and obj.pk else '',
        summary=summary,
        details=details or {},
        ip_address=client_ip(request) if request else None,
    )


def notify(user, title, body='', target_url='', actor=None):
    if user and user.is_active and user.approved:
        Notification.objects.create(recipient=user, actor=actor, title=title, body=body[:4000], target_url=target_url[:500])


def notify_many(users, title, body='', target_url='', actor=None):
    now = timezone.now()
    Notification.objects.bulk_create([
        Notification(recipient=u, actor=actor, title=title, body=body[:4000], target_url=target_url[:500], created_at=now)
        for u in users if u.is_active and u.approved and (not actor or u.pk != actor.pk)
    ])


def find_mentions(text):
    """Resolve @mentions by username, email local-part, or display name with underscores."""
    tokens = set(re.findall(r'@([\w.\-+\u0600-\u06FF]+)', text or '', flags=re.UNICODE))
    found = []
    if not tokens:
        return found
    users = User.objects.filter(is_active=True, approved=True)
    for token in tokens:
        target = token.replace('_', ' ').casefold()
        for user in users:
            aliases = {user.username.casefold(), user.email.split('@')[0].casefold(), user.display_name.replace(' ', '_').casefold(), user.display_name.casefold()}
            if token.casefold() in aliases or target == user.display_name.casefold():
                found.append(user)
                break
    # Preserve order and remove duplicates.
    return list({u.pk: u for u in found}.values())


def parse_mention_ids(raw):
    ids = []
    for part in (raw or '').split(','):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids[:50]


def notify_mentions(text, actor, target_url='', ids=None, where='نظر'):
    """Notify every mentioned user: ids chosen from the @ list plus names/emails typed in the text."""
    targets = {u.pk: u for u in find_mentions(text)}
    for u in User.objects.filter(pk__in=parse_mention_ids(','.join(map(str, ids or []))), is_active=True, approved=True):
        targets[u.pk] = u
    for user in targets.values():
        if user.pk != actor.pk:
            notify(user, f'{actor.display_name} تاسې په یوه {where} کې یاد کړئ',
                   (text or '')[:250], target_url, actor)
    return list(targets.values())
