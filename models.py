import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class Department(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, default='🏢')
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'امریت'
        verbose_name_plural = 'امریتونه'

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Roles(models.TextChoices):
        GM = 'gm', 'عمومي مدیر'
        DEPUTY = 'deputy', 'مرستیال'
        AMIR = 'amir', 'د امریت مدیر'
        EMPLOYEE = 'employee', 'کارکوونکی'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Roles.choices, default=Roles.EMPLOYEE)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT, related_name='members')
    approved = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=2, choices=[('ps','پښتو'),('fa','دری/فارسی'),('ar','العربية'),('en','English')], default='ps')
    calendar_system = models.CharField(max_length=12, choices=[('solar','لمریز'),('gregorian','میلادي'),('lunar','هجري قمري')], default='solar')
    timezone = models.CharField(max_length=64, default='Asia/Kabul')

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def display_name(self):
        return self.get_full_name() or self.email

    @property
    def is_general_manager(self):
        return self.role == self.Roles.GM


class Document(models.Model):
    class Period(models.TextChoices):
        DAILY = 'daily', 'ورځنی'
        WEEKLY = 'weekly', 'اونیز'
        MONTHLY = 'monthly', 'میاشتنی'
        SIX_MONTH = 'six_month', 'شپږمیاشتنی'
        YEARLY = 'yearly', 'کلنی'
        NONE = 'none', 'له راپور سره تړاو نه لري'

    class Status(models.TextChoices):
        PENDING = 'pending', 'د کتنې په تمه'
        VIEWED = 'viewed', 'کتل شوی'

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='documents')
    period = models.CharField(max_length=16, choices=Period.choices, default=Period.NONE)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='documents')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_documents')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['department', 'created_at'], name='doc_dept_date_idx'), models.Index(fields=['status', 'is_archived'], name='doc_status_arch_idx')]
        verbose_name = 'سند / راپور'
        verbose_name_plural = 'اسناد او راپورونه'

    def __str__(self):
        return self.title

    @property
    def viewed(self):
        return self.status == self.Status.VIEWED


def attachment_upload_path(instance, filename):
    safe_name = filename.replace('..', '_').replace('/', '_').replace('\\', '_')[:180]
    return f'attachments/{timezone.now():%Y/%m}/{uuid.uuid4().hex}_{safe_name}'


class Attachment(models.Model):
    document = models.ForeignKey(Document, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    post = models.ForeignKey('Post', null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_upload_path, validators=[FileExtensionValidator(['pdf','doc','docx','xls','xlsx','csv','txt','png','jpg','jpeg','gif','webp','mp4','mov','mp3','wav','ogg','webm','m4a'])])
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_attachments')
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        if bool(self.document_id) == bool(self.post_id):
            from django.core.exceptions import ValidationError
            raise ValidationError('ضمیمه باید یوازې له یوه سند یا خبر سره وتړل شي.')

    def __str__(self):
        return self.original_name


class Post(models.Model):
    class Kind(models.TextChoices):
        GENERAL = 'general', 'عمومي خبر'
        IMPORTANT = 'important', 'مهم خبر'

    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.GENERAL)
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='posts')
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name='posts')
    text = models.TextField(blank=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_posts')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'خبر / اعلان'
        verbose_name_plural = 'خبرونه او اعلانونه'

    def __str__(self):
        return (self.text or self.get_kind_display())[:80]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name='comments')
    text = models.TextField(max_length=3000)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']


class Message(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'text', 'لیکلې'
        VOICE = 'voice', 'غږیز'

    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sent_messages')
    recipient = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='direct_messages')
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE, related_name='messages')
    to_everyone = models.BooleanField(default=False)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.TEXT)
    text = models.TextField(blank=True)
    voice_file = models.FileField(upload_to=attachment_upload_path, blank=True, null=True, validators=[FileExtensionValidator(['mp3','wav','ogg','webm','m4a'])])
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        destinations = int(self.to_everyone) + int(bool(self.department_id)) + int(bool(self.recipient_id))
        if destinations != 1:
            from django.core.exceptions import ValidationError
            raise ValidationError('پیغام باید یو ټاکلی ترلاسه کوونکی ولري.')
        if self.kind == self.Kind.TEXT and not self.text.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError('د پیغام متن تش دی.')
        if self.kind == self.Kind.VOICE and not self.voice_file:
            from django.core.exceptions import ValidationError
            raise ValidationError('غږیز فایل نشته.')


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='triggered_notifications')
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    target_url = models.CharField(max_length=500, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_read(self):
        return self.read_at is not None


class AuditEvent(models.Model):
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    summary = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'د فعالیت ثبت'
        verbose_name_plural = 'د فعالیتونو تاریخچه'

    def __str__(self):
        return f'{self.action}: {self.summary[:70]}'


class ExternalNews(models.Model):
    title = models.CharField(max_length=400)
    summary = models.TextField(blank=True)
    source = models.CharField(max_length=180, blank=True)
    url = models.URLField(max_length=1000, unique=True)
    published_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(default=timezone.now)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at', '-fetched_at']
        verbose_name = 'بهرنی خبر'
        verbose_name_plural = 'بهرني خبرونه'

    def __str__(self):
        return self.title[:100]


class SystemSetting(models.Model):
    system_name = models.CharField(max_length=180, default='د ادارې متحد سیستم')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'د سیستم تنظیم'
        verbose_name_plural = 'د سیستم تنظیمات'

    def __str__(self):
        return self.system_name
