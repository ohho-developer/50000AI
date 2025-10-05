from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    """50000AI 메인 홈페이지"""
    return render(request, 'accounts/home.html')

@login_required
def profile_view(request):
    """사용자 프로필 페이지"""
    return render(request, 'accounts/profile.html')
