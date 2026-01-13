"""
Production settings for deployment.
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# CORS settings for production
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Database configuration for production
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'sslmode': 'require',
    'connect_timeout': 30,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5,
}

# Cache configuration for production
CACHES['default']['LOCATION'] = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
CACHES['default']['OPTIONS'] = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    'SOCKET_CONNECT_TIMEOUT': 5,
    'SOCKET_TIMEOUT': 5,
    'CONNECTION_POOL_KWARGS': {
        'max_connections': 100,
        'retry_on_timeout': True,
    },
}

# Static files with Whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True

# Media files (Use S3 or similar in production)
if os.getenv('USE_S3', 'False').lower() == 'true':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_LOCATION = 'media'
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600  # 1 hour

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Celery configuration for production
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_TIMEOUT = 30
CELERY_BROKER_HEARTBEAT = 300
CELERY_EVENT_QUEUE_EXPIRES = 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Sentry integration (Error monitoring)
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
        send_default_pii=False,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        release=f"crowdfunding-platform@{os.getenv('GIT_COMMIT', '1.0.0')}",
    )

# Logging configuration for production
LOGGING['handlers']['file']['filename'] = '/var/log/crowdfunding/django.log'
LOGGING['handlers']['audit_file']['filename'] = '/var/log/crowdfunding/audit.log'
LOGGING['handlers']['error_file']['filename'] = '/var/log/crowdfunding/error.log'

# Remove console logging in production
LOGGING['handlers'].pop('console', None)
for logger in LOGGING['loggers'].values():
    if 'console' in logger.get('handlers', []):
        logger['handlers'].remove('console')

# API throttling in production
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
    'rest_framework.throttling.ScopedRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/day',
    'user': '1000/day',
    'investment': '10/minute',
    'project_create': '5/hour',
}

# Simple JWT settings for production
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=7)

# API Documentation
SPECTACULAR_SETTINGS['SERVERS'] = [{'url': os.getenv('API_BASE_URL', 'https://api.crowdfunding-platform.com')}]

# Production-specific app settings
APP_SETTINGS['INVESTMENT']['SANDBOX_MODE'] = os.getenv('SANDBOX_MODE', 'True').lower() == 'true'
APP_SETTINGS['DEBUG'] = False

# Load balancing and proxy settings
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')