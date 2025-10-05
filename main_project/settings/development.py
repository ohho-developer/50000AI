"""
Development settings for main_project project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development specific settings
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development database (SQLite)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# Development email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development security settings (disabled for development)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development CSRF settings
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Development logging (reduced verbosity)
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['nutrients_codi']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'INFO'

# Add specific loggers to reduce verbosity
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
LOGGING['loggers']['django.db.migrations'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
