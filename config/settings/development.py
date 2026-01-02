from .base import *
from decouple import config

DEBUG = config('DEBUG', default=True, cast=bool)

# Only allow all origins in development
CORS_ALLOW_ALL_ORIGINS = DEBUG

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0').split(',')

if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']