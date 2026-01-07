# config/settings/development.py
from .base import *
from decouple import config

DEBUG = True


ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0').split(',')

# Only allow all origins in development
CORS_ALLOW_ALL_ORIGINS = DEBUG

if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']

# ===============================
# DATABASE OVERRIDE (if needed for dev)
# ===============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='crowdfunding_db'),
        'USER': config('POSTGRES_USER', default='postgres'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='postgres'),
        'HOST': config('POSTGRES_HOST', default='127.0.0.1'),
        'PORT': config('POSTGRES_PORT', default=5432, cast=int),
    }
}

# ===============================
# CACHES (optional for dev)
# ===============================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ===============================
# EMAIL BACKEND (console for dev)
# ===============================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
