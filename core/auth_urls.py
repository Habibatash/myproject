from django.urls import path
from . import auth_views, views

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('resend-verification/', auth_views.resend_verification, name='resend_verification'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
]
