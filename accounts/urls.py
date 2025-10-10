from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
]
