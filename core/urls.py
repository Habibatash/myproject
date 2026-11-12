from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('documents/', views.documents, name='documents'),
    path('reports/', views.reports, name='reports'),
    path('departments/', views.departments, name='departments'),
    path('archive/', views.archive, name='archive'),
    path('news/', views.news, name='news'),
    path('important-news/', views.news, name='important_news'),
    path('users/', views.users_page, name='users'),
    path('messages/', views.messages_page, name='messages'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('ai/', views.ai_page, name='ai'),
    path('office/', views.office, name='office'),
    path('world-news/', views.world_news, name='world_news'),
    path('api/mention-users/', views.mention_users, name='mention_users'),
    path('api/notifications/poll/', views.notifications_poll, name='notifications_poll'),
    path('audit/', views.audit_page, name='audit'),
    path('settings/', views.settings_page, name='settings'),
    path('attachment/<int:pk>/download/', views.attachment_download, name='attachment_download'),
    path('message/<int:pk>/voice/', views.message_voice, name='message_voice'),
    
    # د لاګین سم مسیر د login.html فایل سره:
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
]
