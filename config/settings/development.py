from .base import *
from decouple import config
import datetime


DEBUG = config('DEBUG', default=True, cast=bool)


CORS_ALLOW_ALL_ORIGINS = True


ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


DATABASES['default']['HOST'] = 'localhost'


FRONTEND_URL = 'http://localhost:3000'


if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']


SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = datetime.timedelta(
    minutes=config('SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)
)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = datetime.timedelta(
    days=config('SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
)