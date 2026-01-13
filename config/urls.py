"""
URL configuration for Crowdfunding Trading Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication endpoints
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints (Organized by SRS modules)
    path('api/users/', include('apps.users.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/investments/', include('apps.investments.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/access-requests/', include('apps.access_requests.urls')),
    path('api/favorites/', include('apps.favorites.urls')),
    path('api/comparisons/', include('apps.comparisons.urls')),
    
    # Health check endpoint
    path('health/', include('health_check.urls')),
]

# Debug toolbar
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site configuration
admin.site.site_header = 'Crowdfunding Trading Platform Administration'
admin.site.site_title = 'Crowdfunding Admin'
admin.site.index_title = 'Platform Management'