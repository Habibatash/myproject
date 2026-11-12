from django import template
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
