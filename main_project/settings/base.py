"""
Base settings for main_project project.
"""

from pathlib import Path
import os
import sys
from decouple import config

# UTF-8 인코딩 강제 설정 (Windows 환경)
if sys.platform == 'win32':
    import locale
    # Python 3.7+ 에서만 작동
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-65o@asf)%-(11y*d1zq#nhsqaut0a#s@8ziht$l_86m!wa757m')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Local apps
    'accounts',
    'nutrients_codi',
    'recipe_ai',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise 추가 (정적 파일 서빙)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
        # 연결 풀링 최적화 (60초 유지)
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'options': "-c search_path=schema_a,public",
            # PostgreSQL 성능 최적화
            'connect_timeout': 10,
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'  # Default language
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Supported languages
LANGUAGES = [
    ('ko', '한국어'),
    ('en', 'English'),
]

# Language cookie settings (optional but recommended)
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = None  # Session cookie
LANGUAGE_COOKIE_DOMAIN = None
LANGUAGE_COOKIE_PATH = '/'

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# WhiteNoise 설정 (프로덕션에서 정적 파일 서빙)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sites framework
SITE_ID = 1

# Django Allauth settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth configuration (django-allauth 65+ 새 형식)
ACCOUNT_LOGIN_METHODS = {'email', 'username'}  # 이메일 또는 username으로 로그인
ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']  # 회원가입 필수 필드
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/m',  # 로그인 실패 제한
    'confirm_email': '3/m',  # 이메일 확인 제한
}
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/nutrients-codi/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/nutrients-codi/'

# Allauth messages
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Allauth form settings
ACCOUNT_FORMS = {
    'login': 'allauth.account.forms.LoginForm',
    'signup': 'allauth.account.forms.SignupForm',
}

# Allauth login settings
ACCOUNT_LOGIN_ON_GET = False
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = True
# ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # 주석 처리 - 기본값(username) 사용
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')

# Allauth email settings
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[50000AI] '
ACCOUNT_EMAIL_CONFIRMATION_SUBJECT = '이메일 주소 확인'
ACCOUNT_EMAIL_CONFIRMATION_MESSAGE = '이메일 주소를 확인하려면 아래 링크를 클릭하세요:'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_SUBJECT = '새 이메일 주소 확인'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_MESSAGE = '새 이메일 주소를 확인하려면 아래 링크를 클릭하세요:'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

# Google Gemini API
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# YouTube Data API
YOUTUBE_API_KEY = config('GEMINI_API_KEY', default='')

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default=None)
if SECURE_PROXY_SSL_HEADER:
    SECURE_PROXY_SSL_HEADER = tuple(SECURE_PROXY_SSL_HEADER.split(','))
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)

# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)

# CSRF security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000,http://127.0.0.1:8000').split(',') if config('CSRF_TRUSTED_ORIGINS', default='') else []

# X-Frame-Options
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Logging configuration (console only for deployment)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'nutrients_codi': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'api_cache_table',
        'TIMEOUT': 604800,  # 24시간 (초 단위)
        'OPTIONS': {
            'MAX_ENTRIES': 1000  # 최대 1000개 캐시 항목
        }
    }
}
