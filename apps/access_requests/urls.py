"""
Access Request URL Configuration
Clean, organized routing with proper namespace
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccessRequestViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', AccessRequestViewSet, basename='access-request')

# Custom URL patterns for additional actions
urlpatterns = [
    path('', include(router.urls)),
]