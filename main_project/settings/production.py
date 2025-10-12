"""
Production settings for main_project project.
"""

from .base import *
import sys
import locale

# 프로덕션 환경에서 UTF-8 인코딩 강제 설정
try:
    if sys.getdefaultencoding() != 'utf-8':
        import importlib
        importlib.reload(sys)
except:
    pass

# 환경 변수로 UTF-8 설정
import os
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False)

# Production security settings (disabled for Cloudtype.app)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)  # Cloudtype handles SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Cloudtype proxy header
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# Session security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)

# CSRF security
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)


# Database 성능 최적화 (WORKER TIMEOUT 방지)
DATABASES['default']['CONN_MAX_AGE'] = 60  # 연결 풀링
if 'OPTIONS' not in DATABASES['default']:
    DATABASES['default']['OPTIONS'] = {}
DATABASES['default']['OPTIONS'].update({
    'connect_timeout': 10,
})

# 캐시 설정 강화 (메모리 효율성)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'api_cache_table',
        'TIMEOUT': 3600,  # 1시간
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Production logging (console only, less verbose)
LOGGING['handlers']['console']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['nutrients_codi']['level'] = 'INFO'
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],  # file → console로 수정
    'level': 'ERROR',  # DB 쿼리 로그 최소화 (메모리 절약)
    'propagate': False,
}
LOGGING['root']['level'] = 'WARNING'



# Session engine (using database for simplicity)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Production static files (WhiteNoise로 처리)
# STATICFILES_STORAGE는 base.py에서 설정됨

# Production media files (use cloud storage in production)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
# AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-northeast-2')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
