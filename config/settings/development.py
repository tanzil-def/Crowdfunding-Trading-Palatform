"""
Development settings for local development.
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable SSL in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django Debug Toolbar (Optional)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Database configuration for development
DATABASES['default']['CONN_MAX_AGE'] = 60

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging configuration for development
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Simple JWT settings for development
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(days=1)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)

# Celery configuration for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# API Documentation
SPECTACULAR_SETTINGS['SERVERS'] = [{'url': 'http://localhost:8000'}]

# Development-specific app settings
APP_SETTINGS['INVESTMENT']['SANDBOX_MODE'] = True
APP_SETTINGS['DEBUG'] = True