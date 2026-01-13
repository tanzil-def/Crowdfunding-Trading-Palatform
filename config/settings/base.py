"""
Base settings for Crowdfunding Trading Platform.

Contains all common settings across environments.
SRS Compliant: Security, Performance, Reliability requirements.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # Override in environment-specific files

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    
    # Local Apps (SRS Modules)
    'apps.users',
    'apps.projects',
    'apps.investments',
    'apps.dashboard',
    'apps.notifications',
    'apps.audit',
    'apps.access_requests',
    'apps.favorites',
     #'apps.comparisons',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom Middleware
    'utils.middleware.RequestLoggingMiddleware',
    'utils.middleware.UserActivityMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'crowdfunding_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection persistence
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'crowdfunding_platform',
        }
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # SRS: Secure password requirements
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings (SRS: Media size limits)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880   # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',
    
    # Security settings
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False  # Only for development
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Disposition']

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@crowdfunding-platform.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Frontend URL (For email links)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'crowdfunding',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = []

# File Storage (For production, use S3 or similar)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'audit': {
            'format': '{asctime} - {levelname} - {name} - {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'audit',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# API Documentation (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Crowdfunding Trading Platform API',
    'DESCRIPTION': 'API documentation for the Crowdfunding Trading Platform (SRS Compliant)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
    ],
    'ENUM_NAME_OVERRIDES': {
        'UserRoleEnum': 'apps.users.models.User.Role',
        'ProjectStatusEnum': 'apps.projects.models.Project.Status',
        'InvestmentStatusEnum': 'apps.investments.models.Investment.Status',
    },
}

# Application-specific settings (SRS Compliance)
APP_SETTINGS = {
    # Project settings
    'MAX_PROJECTS_PER_DEVELOPER': 10,
    'PROJECT_DURATION_MIN_DAYS': 30,
    'PROJECT_DURATION_MAX_DAYS': 365 * 5,  # 5 years
    
    # Media upload limits (SRS: File size and format limits)
    'MEDIA': {
        'MAX_IMAGE_SIZE': 5 * 1024 * 1024,  # 5MB
        'MAX_3D_MODEL_SIZE': 50 * 1024 * 1024,  # 50MB
        'ALLOWED_IMAGE_EXTENSIONS': ['jpg', 'jpeg', 'png', 'webp'],
        'ALLOWED_3D_EXTENSIONS': ['glb', 'gltf', 'obj'],
    },
    
    # Investment settings (SRS: Share-based model)
    'INVESTMENT': {
        'MIN_SHARES_PER_INVESTMENT': 1,
        'MAX_SHARES_PER_INVESTMENT': 100000,
        'APPROVAL_EXPIRY_DAYS': 7,
        'SANDBOX_MODE': True,  # SRS: Sandbox-only in MVP
    },
    
    # Payment settings
    'PAYMENT': {
        'SANDBOX_GATEWAY_URL': 'https://api.sandbox.payment-gateway.com',
        'PRODUCTION_GATEWAY_URL': 'https://api.payment-gateway.com',
        'CALLBACK_TIMEOUT': 30,  # seconds
    },
    
    # Dashboard settings
    'DASHBOARD': {
        'UPDATE_INTERVAL_MINUTES': 5,
        'CACHE_TTL_HOURS': 1,
    },
    
    # Notification settings
    'NOTIFICATIONS': {
        'RETENTION_DAYS': 90,
        'BATCH_SIZE': 50,
    },
    
    # Security settings (SRS: Security requirements)
    'SECURITY': {
        'PASSWORD_RESET_TIMEOUT_MINUTES': 1440,  # 24 hours
        'EMAIL_VERIFICATION_TIMEOUT_MINUTES': 1440,  # 24 hours
        'MAX_LOGIN_ATTEMPTS': 5,
        'LOCKOUT_TIME_MINUTES': 30,
    },
}