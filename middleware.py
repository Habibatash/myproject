from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils import timezone

class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.deactivate()
        if getattr(request, 'user', None) is not None and request.user.is_authenticated:
            try:
                timezone.activate(ZoneInfo(request.user.timezone or 'Asia/Kabul'))
            except (ZoneInfoNotFoundError, ValueError):
                timezone.activate(ZoneInfo('Asia/Kabul'))
        return self.get_response(request)
