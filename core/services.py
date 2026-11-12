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


def notify_mentions(text, actor, target_url=''):
    for user in find_mentions(text):
        if user.pk != actor.pk:
            notify(user, 'تاسې په یوه پیغام کې یاد شوي یاست', f'{actor.display_name}: {(text or "")[:180]}', target_url, actor)
