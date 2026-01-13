"""
Test settings for running tests.
"""

from .base import *

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email sending
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable throttling for tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Celery configuration for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test-specific app settings
APP_SETTINGS['INVESTMENT']['SANDBOX_MODE'] = True
APP_SETTINGS['DEBUG'] = True