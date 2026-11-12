from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from .models import Department, User
from .services import audit

def _send_verification(request, user):
    token = TimestampSigner().sign(str(user.pk))
    link = request.build_absolute_uri(reverse('verify_email', args=[token]))
    send_mail('د ادارې متحد سیستم - ایمیل تایید',
              f'سلام {user.display_name}،\n\nد خپل ایمیل د تایید لپاره دا لینک خلاص کړئ (۴۸ ساعته اعتبار لري):\n{link}\n\nکه تاسې دا حساب نه دی جوړ کړی، دا ایمیل له پامه وغورځوئ.',
              settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


@require_http_methods(['GET','POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    unverified_email = ''
    if request.method == 'POST':
        identity = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = User.objects.filter(email__iexact=identity).first() or User.objects.filter(username__iexact=identity).first()
        if not user:
            User().set_password(password)  # keep timing similar for unknown accounts
        if not user or not user.check_password(password):
            messages.error(request, 'ایمیل یا پټنوم ناسم دی.')
        elif settings.EMAIL_VERIFICATION_REQUIRED and not user.email_verified and not user.is_superuser:
            unverified_email = user.email
            messages.error(request, 'لومړی خپل ایمیل تایید کړئ؛ د تایید لینک ستاسې ایمیل ته لېږل شوی دی.')
        elif not user.approved:
            messages.error(request, 'ستاسې حساب لا د عمومي مدیر له خوا نه دی تایید شوی.')
        elif not user.is_active:
            messages.error(request, 'حساب غیرفعال دی؛ له عمومي مدیر سره اړیکه ونیسئ.')
        else:
            login(request, user, backend='core.backends.EmailOrUsernameBackend')
            return redirect('dashboard')
    return render(request, 'core/login.html', {'unverified_email': unverified_email})


@require_POST
def resend_verification(request):
    email = request.POST.get('email', '').strip().lower()
    user = User.objects.filter(email__iexact=email, email_verified=False).first()
    if user and settings.EMAIL_VERIFICATION_REQUIRED:
        try:
            _send_verification(request, user)
        except Exception:
            messages.warning(request, 'ایمیل ونه لېږل شو. د SMTP تنظیمات وګورئ.')
            return redirect('login')
    messages.success(request, 'که دا ایمیل ثبت او نه تایید شوی وي، د تایید لینک بیا ورته ولېږل شو.')
    return redirect('login')


@require_http_methods(['GET','POST'])
def register_view(request):
    departments = Department.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name','').strip()
        email = request.POST.get('email','').strip().lower()
        department_id = request.POST.get('department')
        password = request.POST.get('password','')
        confirm = request.POST.get('confirm_password','')
        if not name or not email or not department_id or len(password) < 10 or password != confirm:
            messages.error(request, 'ټول ځایونه ډک کړئ؛ پټنوم لږ تر لږه ۱۰ توري او دواړه پټنومونه یو شان وي.')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'دا ایمیل مخکې ثبت شوی دی.')
        else:
            dept = departments.filter(pk=department_id).first()
            if not dept:
                messages.error(request, 'سم امریت وټاکئ.')
            else:
                first, *rest = name.split(' ', 1)
                user = User.objects.create_user(username=email, email=email, first_name=first, last_name=rest[0] if rest else '',
                    department=dept, role=User.Roles.EMPLOYEE, approved=False, email_verified=False, is_active=False)
                user.set_password(password); user.save()
                if settings.EMAIL_VERIFICATION_REQUIRED:
                    try:
                        _send_verification(request, user)
                        messages.success(request, 'حساب ثبت شو. د تایید لینک ستاسې ایمیل ته ولېږل شو؛ لومړی ایمیل تایید کړئ او بیا د عمومي مدیر تایید ته انتظار وکړئ.')
                    except Exception:
                        messages.warning(request, 'حساب ثبت شو، خو ایمیل ونه لېږل شو. د SMTP تنظیمات وګورئ (په console backend کې لینک د سرور په لاګ کې ښکاري).')
                else:
                    messages.success(request, 'حساب ثبت شو؛ د عمومي مدیر له تایید وروسته به ننوتلای شئ.')
                audit(request, 'registration', f'د حساب د ثبت غوښتنه: {email}', user)
                return redirect('login')
    return render(request, 'core/register.html', {'departments':departments})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
