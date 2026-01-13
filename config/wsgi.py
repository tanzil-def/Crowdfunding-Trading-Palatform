"""
WSGI config for Crowdfunding Trading Platform.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()

# WhiteNoise for serving static files
try:
    from whitenoise import WhiteNoise
    from django.conf import settings
    application = WhiteNoise(
        application,
        root=settings.STATIC_ROOT,
        prefix=settings.STATIC_URL,
        max_age=31536000 if not settings.DEBUG else 0,
    )
except ImportError:
    pass