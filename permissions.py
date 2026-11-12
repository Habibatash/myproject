from django.db.models import Q
from .models import Document, Message, User


def is_gm(user):
    return bool(user.is_authenticated and user.role == User.Roles.GM)


def is_deputy(user):
    return bool(user.is_authenticated and user.role == User.Roles.DEPUTY)


def is_employee_level(user):
    """The source prototype treats deputy and employee identically for data access."""
    return bool(user.is_authenticated and user.role in {User.Roles.EMPLOYEE, User.Roles.DEPUTY})


def can_manage_users(user):
    return is_gm(user)


def can_send_messages(user):
    # In the original interface only the general manager and department manager can compose.
    return bool(user.is_authenticated and user.role in {User.Roles.GM, User.Roles.AMIR})


def visible_documents(user):
    qs = Document.objects.select_related('department', 'created_by', 'reviewed_by').prefetch_related('attachments')
    if is_gm(user):
        return qs
    if user.role == User.Roles.AMIR:
        # A department manager sees their own records and records submitted by
        # employees/deputies in their own department, not records of other managers.
        return qs.filter(
            Q(created_by=user) |
            Q(department_id=user.department_id,
              created_by__role__in=[User.Roles.EMPLOYEE, User.Roles.DEPUTY])
        )
    return qs.filter(created_by=user)


def can_view_document(user, document):
    if is_gm(user):
        return True
    if user.role == User.Roles.AMIR:
        own = document.created_by_id == user.id
        staff_record = bool(
            user.department_id and document.department_id == user.department_id and
            document.created_by.role in {User.Roles.EMPLOYEE, User.Roles.DEPUTY}
        )
        return own or staff_record
    return document.created_by_id == user.id


def can_edit_document(user, document):
    return can_view_document(user, document)


def visible_messages(user):
    access = Q(sender=user) | Q(recipient=user) | Q(to_everyone=True)
    # Department broadcasts are delivered only to employee-level accounts in that department.
    if is_employee_level(user) and user.department_id:
        access |= Q(department_id=user.department_id)
    return Message.objects.filter(access).select_related('sender', 'recipient', 'department')


def can_edit_post(user, post):
    if is_gm(user) or post.author_id == user.id:
        return True
    return bool(
        user.role == User.Roles.AMIR and user.department_id == post.department_id and
        post.author.department_id == user.department_id and
        post.author.role in {User.Roles.EMPLOYEE, User.Roles.DEPUTY}
    )


def can_delete_comment(user, comment):
    """Match the prototype: GM, author, or same-department Amir can remove it."""
    if is_gm(user) or comment.author_id == user.pk:
        return True
    return bool(
        user.is_authenticated and user.role == User.Roles.AMIR and
        user.department_id and comment.author.department_id == user.department_id and
        comment.author.role in {User.Roles.EMPLOYEE, User.Roles.DEPUTY}
    )
