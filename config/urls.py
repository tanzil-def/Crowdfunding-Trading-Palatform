from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # API v1 - Auth
    path('api/v1/auth/', include('apps.users.urls', namespace='auth')),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # duplicate for convenience
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# ==================== DEVELOPMENT ONLY SETTINGS ====================
if settings.DEBUG:
    # Serve media & static files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # === DJANGO DEBUG TOOLBAR URLs (এটাই missing ছিল) ===
    # 'djdt' namespace register করার জন্য এই line টা অবশ্যই লাগবে
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar  
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),  # <-- এই line যোগ করো
        ] + urlpatterns