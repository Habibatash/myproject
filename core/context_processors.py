from .models import SystemSetting, Notification

def site_context(request):
    setting = SystemSetting.objects.first()
    context = {'site_name': setting.system_name if setting else 'د ادارې متحد سیستم', 'unread_notifications': 0}
    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return context
