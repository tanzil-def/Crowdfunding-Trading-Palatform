from .base import *

DEBUG = False
SECRET_KEY = 'test-secret-key-for-running-tests'

# Use SQLite for tests to avoid permission issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3', 
    }
}

# Use locmem for email testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
