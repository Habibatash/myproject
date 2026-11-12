from django.contrib.auth.backends import ModelBackend
from .models import User

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identity = (username or kwargs.get('email') or '').strip()
        if not identity or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=identity)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=identity)
            except User.DoesNotExist:
                User().set_password(password)
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
