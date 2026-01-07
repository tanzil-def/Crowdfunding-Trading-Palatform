# config/settings/development.py
from .base import *
<<<<<<< HEAD
from decouple import config
=======

# ===============================
# DEBUG SETTINGS
# ===============================
DEBUG = True
>>>>>>> 83d38a9 (WIP: work in progress on project features)

# ===============================
# ALLOWED HOSTS
# ===============================
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

<<<<<<< HEAD
# Only allow all origins in development
CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOW_ALL_ORIGINS = True


ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


DATABASES['default']['HOST'] = 'localhost'


FRONTEND_URL = 'http://localhost:3000'


if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']
=======
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
# DEV-SPECIFIC SETTINGS
# ===============================
# No need to append debug_toolbar here
# base.py already handles:
#   - Adding debug_toolbar to INSTALLED_APPS if DEBUG=True
#   - Adding DebugToolbarMiddleware
#   - INTERNAL_IPS for 127.0.0.1

# ===============================
# EMAIL BACKEND (console for dev)
# ===============================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
>>>>>>> 83d38a9 (WIP: work in progress on project features)
