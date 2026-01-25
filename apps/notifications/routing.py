"""
Django Channels routing configuration for WebSocket endpoints.
"""
from django.urls import path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
