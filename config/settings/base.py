# config/settings/base.py
from pathlib import Path
from decouple import config, Csv
import datetime

# ------------------ BASE ------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ------------------ SECURITY ------------------
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ------------------ APPS ------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',  # Must be before local apps for proper schema generation

    # Local apps
    'apps.users',
    'apps.projects',
    'apps.favorites',
    'apps.access_requests',
    'apps.investments',
    'apps.notifications',
    'apps.audit',
    'apps.dashboard',
]

# ------------------ MIDDLEWARE ------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------ URLS & TEMPLATES ------------------
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

# ------------------ DATABASE ------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}

# ------------------ PASSWORD VALIDATION ------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------ INTERNATIONALIZATION ------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------ STATIC & MEDIA ------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------ DEFAULT PK ------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------ CUSTOM USER ------------------
AUTH_USER_MODEL = 'users.CustomUser'

# ------------------ REST FRAMEWORK ------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ------------------ DRF SPECTACULAR (Swagger/OpenAPI) ------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'Crowdfunding Trading Platform API',
    'DESCRIPTION': 'Equity-based crowdfunding platform with role-based access, restricted content, share investing, and admin governance.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },

    # CRITICAL SETTINGS FOR FILE UPLOADS & CUSTOM ACTIONS
    'COMPONENT_SPLIT_REQUEST': True,  # Essential for multipart/form-data (file upload) in Swagger
    'SCHEMA_PATH_PREFIX': '/api/v1/',  # Groups all APIs under /api/v1/

    # Ensures @action endpoints are properly included
    'PREPROCESSING_HOOKS': [
        'drf_spectacular.hooks.preprocess_exclude_path_format',
    ],

    # Better support for form data
    'PARSER_CONTENT_TYPES': {
        'multipart/form-data': 'multipart',
        'application/x-www-form-urlencoded': 'form',
    },

    'APPEND_SCHEMA_REQUEST_BODY': True,
}

# ------------------ CORS (Development only) ------------------
CORS_ALLOW_ALL_ORIGINS = True  # WARNING: Restrict in production!

# ------------------ SIMPLE JWT ------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=config('ACCESS_TOKEN_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=config('REFRESH_TOKEN_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ------------------ EMAIL ------------------
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@crowdfundingplatform.com')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES = 60
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 60

# ------------------ MEDIA UPLOAD LIMITS ------------------
MAX_UPLOAD_SIZE = 1024 * 1024 * 50  # 50 MB general limit
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
ALLOWED_3D_TYPES = ['model/gltf-binary', 'model/gltf+json', 'application/octet-stream']  # .glb/.gltf
MAX_3D_SIZE = 1024 * 1024 * 100  # 100 MB for 3D models

# Project-specific media limits (used in ProjectMedia validation)
PROJECT_MEDIA_MAX_SIZE_MB = 50
PROJECT_MEDIA_ALLOWED_IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
PROJECT_MEDIA_ALLOWED_3D_EXT = ['.glb', '.gltf']
PROJECT_MEDIA_ALLOWED_VIDEO_EXT = ['.mp4', '.webm', '.mov']