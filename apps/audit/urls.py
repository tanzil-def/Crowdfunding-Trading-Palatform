from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, SystemHealthLogViewSet

# Create routers
router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')
router.register(r'health', SystemHealthLogViewSet, basename='system-health')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]