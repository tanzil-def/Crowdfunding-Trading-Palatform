from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectMediaViewSet

router = DefaultRouter(trailing_slash=True)

# Register Developer projects first
router.register(r'projects', ProjectViewSet, basename='projects')

# Register Project Media second
router.register(r'project-media', ProjectMediaViewSet, basename='project-media')

urlpatterns = router.urls
