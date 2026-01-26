from django.urls import path
from .views import ProjectViewSet, AdminProjectViewSet
from apps.access_requests.views import DeveloperProjectAccessRequestListView


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
    path('<uuid:pk>/media/<uuid:media_id>/', ProjectViewSet.as_view({'delete': 'delete_media'}), name='project-media-delete'),
    path('<uuid:pk>/media/<uuid:media_id>/toggle-restriction/', ProjectViewSet.as_view({'patch': 'toggle_media_restriction'}), name='project-media-toggle-restriction'),
    path('<uuid:pk>/investments/', ProjectViewSet.as_view({'get': 'investments'}), name='project-investments'),
    path('<uuid:project_id>/access-requests/', DeveloperProjectAccessRequestListView.as_view(), name='project-access-requests'),

    
    # Investor Specific
    # Explicit 'detail' path from OAS
    path('<uuid:pk>/detail/', ProjectViewSet.as_view({'get': 'retrieve'}), name='project-detail'),
    # Explicit 'browse' path from OAS (Alias to list)
    path('browse/', ProjectViewSet.as_view({'get': 'list'}), name='investor-browse-projects'),
    path('compare/', ProjectViewSet.as_view({'get': 'compare'}), name='investor-compare-projects'),
    path('categories/', ProjectViewSet.as_view({'get': 'categories'}), name='project-categories'),

    # Admin Routes
    path('admin/projects/', AdminProjectViewSet.as_view({'get': 'list'}), name='admin-all-projects'),
    path('admin/projects/pending/', AdminProjectViewSet.as_view({'get': 'pending_projects'}), name='admin-pending-projects'),
    path('admin/projects/statistics/', AdminProjectViewSet.as_view({'get': 'statistics'}), name='admin-project-statistics'),
    path('admin/projects/<uuid:pk>/approve/', AdminProjectViewSet.as_view({'post': 'approve'}), name='admin-approve-project'),
    path('admin/projects/<uuid:pk>/reject/', AdminProjectViewSet.as_view({'post': 'reject'}), name='admin-reject-project'),
    path('admin/projects/<uuid:pk>/request-changes/', AdminProjectViewSet.as_view({'post': 'request_changes'}), name='admin-request-changes'),
    path('admin/projects/<uuid:pk>/archive/', AdminProjectViewSet.as_view({'post': 'archive'}), name='admin-archive-project'),
]