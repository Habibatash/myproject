from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (Attachment, AuditEvent, Comment, Department, Document, ExternalNews,
                     Message, Notification, Post, SystemSetting, User)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('email','first_name','last_name','role','department','approved','is_active','is_staff')
    list_filter = ('role','department','approved','is_active')
    search_fields = ('email','first_name','last_name')
    ordering = ('email',)
    fieldsets = DjangoUserAdmin.fieldsets + (('د ادارې معلومات', {'fields': ('role','department','approved','email_verified','preferred_language','calendar_system','timezone')}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (('د ادارې معلومات', {'fields': ('email','first_name','last_name','role','department','approved','email_verified')}),)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name','slug','sort_order','is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('sort_order','is_active')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title','department','period','created_by','status','is_archived','created_at')
    list_filter = ('department','period','status','is_archived')
    search_fields = ('title','description','created_by__email')
    readonly_fields = ('created_at','updated_at')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('kind','author','department','created_at')
    list_filter = ('kind','department')
    search_fields = ('text','author__email')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post','author','created_at')
    search_fields = ('text','author__email')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_name','uploaded_by','size','created_at')
    readonly_fields = ('file','original_name','content_type','size','uploaded_by','created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender','recipient','department','to_everyone','kind','created_at')
    list_filter = ('kind','to_everyone')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient','title','read_at','created_at')
    list_filter = ('read_at',)

@admin.register(ExternalNews)
class ExternalNewsAdmin(admin.ModelAdmin):
    list_display = ('title','source','published_at','is_featured')
    list_filter = ('is_featured','source')
    search_fields = ('title','summary','source')

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('created_at','actor','action','summary','object_type','object_id')
    list_filter = ('action',)
    search_fields = ('summary','actor__email')
    readonly_fields = ('actor','action','object_type','object_id','summary','details','ip_address','created_at')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('system_name','updated_by','updated_at')
    readonly_fields = ('updated_by','updated_at')
