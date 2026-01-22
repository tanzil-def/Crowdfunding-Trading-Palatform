from django.urls import path
from .views import ProjectViewSet, AdminProjectViewSet

urlpatterns = [
    # General Projects (Create, List/Browse)
    # Fixes 405 error: Now supports GET for browsing and POST for creating
    path('', ProjectViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='project-list-create'),

    # Developer Specific
    path('my/', ProjectViewSet.as_view({'get': 'my_projects'}), name='my-projects'),
    
    # Project Update (PUT/PATCH)
    path('<uuid:pk>/', ProjectViewSet.as_view({
        'put': 'update',
        'patch': 'partial_update'
    }), name='project-update'),

    # Project Actions
    path('<uuid:pk>/submit/', ProjectViewSet.as_view({'post': 'submit'}), name='project-submit'),
    path('<uuid:pk>/media/', ProjectViewSet.as_view({'post': 'upload_media'}), name='project-media-upload'),
    path('<uuid:pk>/media/list/', ProjectViewSet.as_view({'get': 'list_media'}), name='project-media-list'),
    
    # Investor Specific
    # Explicit 'detail' path from OAS
    path('<uuid:pk>/detail/', ProjectViewSet.as_view({'get': 'retrieve'}), name='project-detail'),
    # Explicit 'browse' path from OAS (Alias to list)
    path('browse/', ProjectViewSet.as_view({'get': 'list'}), name='investor-browse-projects'),
    path('compare/', ProjectViewSet.as_view({'get': 'compare'}), name='investor-compare-projects'),

    # Admin Routes
    path('admin/projects/pending/', AdminProjectViewSet.as_view({'get': 'pending_projects'}), name='admin-pending-projects'),
    path('admin/projects/<uuid:pk>/approve/', AdminProjectViewSet.as_view({'post': 'approve'}), name='admin-approve-project'),
    path('admin/projects/<uuid:pk>/reject/', AdminProjectViewSet.as_view({'post': 'reject'}), name='admin-reject-project'),
    path('admin/projects/<uuid:pk>/request-changes/', AdminProjectViewSet.as_view({'post': 'request_changes'}), name='admin-request-changes'),
]