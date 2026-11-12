from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from getpass import getpass
from core.models import User

class Command(BaseCommand):
    help = 'لومړی عمومي مدیر په خوندي ډول جوړوي.'
    def add_arguments(self, parser):
        parser.add_argument('--email')
        parser.add_argument('--name')
    def handle(self, *args, **opts):
        email = (opts.get('email') or input('د عمومي مدیر ایمیل: ')).strip().lower()
        name = (opts.get('name') or input('بشپړ نوم: ')).strip()
        if not email or not name: raise CommandError('ایمیل او نوم ضروري دي.')
        if User.objects.filter(email__iexact=email).exists(): raise CommandError('دا ایمیل مخکې ثبت دی.')
        password = getpass('قوي پټنوم (۱۰+ توري): ')
        confirm = getpass('پټنوم بیا ولیکئ: ')
        if password != confirm: raise CommandError('پټنومونه برابر نه دي.')
        first, *rest = name.split(' ',1)
        probe = User(username=email,email=email,first_name=first,last_name=rest[0] if rest else '')
        try: validate_password(password, probe)
        except ValidationError as e: raise CommandError('; '.join(e.messages))
        u = User.objects.create_superuser(username=email,email=email,password=password,first_name=first,last_name=rest[0] if rest else '',role=User.Roles.GM,approved=True,email_verified=True,is_active=True)
        self.stdout.write(self.style.SUCCESS(f'عمومي مدیر جوړ شو: {u.email}'))
