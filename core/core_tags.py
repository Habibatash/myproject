import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from core.permissions import can_edit_document, can_edit_post as permission_can_edit_post, can_delete_comment as permission_can_delete_comment

register = template.Library()

@register.filter
def can_edit_doc(user, document):
    try:
        return can_edit_document(user, document)
    except Exception:
        return False

@register.filter
def can_edit_post(user, post):
    try:
        return permission_can_edit_post(user, post)
    except Exception:
        return False


@register.filter
def can_delete_comment(user, comment):
    try:
        return permission_can_delete_comment(user, comment)
    except Exception:
        return False


_MENTION_RE = re.compile(r'(@[\w.\-+\u0600-\u06FF]+)', re.UNICODE)


@register.filter
def mentions(value):
    """Escape the text, keep line breaks and highlight @mentions."""
    html = escape(value or '')
    html = _MENTION_RE.sub(r'<span class="mention">\1</span>', html).replace('\n', '<br>')
    return mark_safe(html)
