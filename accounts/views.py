from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from allauth.account.models import EmailAddress, EmailConfirmationHMAC

# Create your views here.

def home(request):
    """50000AI 메인 홈페이지"""
    return render(request, 'main_project/home.html')

def privacy_policy(request):
    """개인정보처리방침 페이지"""
    return render(request, 'main_project/privacy_policy.html')

def terms_of_service(request):
    """이용약관 페이지"""
    return render(request, 'main_project/terms_of_service.html')

def robots_txt(request):
    """robots.txt 파일 제공"""
    from django.http import HttpResponse
    from pathlib import Path
    
    robots_path = Path(__file__).resolve().parent.parent / 'templates' / 'robots.txt'
    with open(robots_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return HttpResponse(content, content_type='text/plain; charset=utf-8')

def sitemap_xml(request):
    """sitemap.xml 파일 제공"""
    domain = request.build_absolute_uri('/').rstrip('/')
    return render(request, 'sitemap.xml', {
        'domain': domain
    }, content_type='application/xml')

@login_required
def profile_view(request):
    """사용자 프로필 페이지"""
    return render(request, 'main_project/profile.html')

@require_http_methods(["POST"])
def resend_verification_email(request):
    """인증 이메일 재발송 (로그인 불필요)"""
    email = request.POST.get('email', '')
    
    if not email:
        # 로그인된 경우 사용자의 이메일 사용
        if request.user.is_authenticated:
            email = request.user.email
        else:
            messages.error(request, "이메일 주소를 입력해주세요.")
            return redirect('account_email_verification_sent')
    
    try:
        # 이메일로 사용자 찾기
        email_address = EmailAddress.objects.get(email=email, primary=True)
        
        if email_address.verified:
            messages.info(request, "이미 인증된 이메일 주소입니다.")
            return redirect('account_login')
        
        # 인증 이메일 재발송 (django-allauth 65+)
        confirmation = EmailConfirmationHMAC(email_address)
        confirmation.send(request)
        messages.success(request, "인증 이메일을 다시 보냈습니다. 받은 편지함을 확인해주세요.")
        
    except EmailAddress.DoesNotExist:
        messages.error(request, "등록되지 않은 이메일 주소입니다.")
    except Exception as e:
        messages.error(request, f"이메일 발송 중 오류가 발생했습니다: {str(e)}")
    
    return redirect('account_email_verification_sent')
