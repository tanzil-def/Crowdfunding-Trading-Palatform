from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView,
    ProjectUpdateView, ProjectSubmitView,
    DeveloperProjectsView, DeveloperDashboardView,
    AdminProjectReviewView, AdminPendingProjectsView,
    AdminProjectArchiveView,
    FavoriteListView, FavoriteDeleteView,
    ComparisonViewSet,
    RestrictedAccessRequestView, RestrictedAccessReviewView,
    AdminAccessRequestsView,
    ProjectMediaUploadView,
    InvestorDashboardView, ProjectStatisticsView,
    Project3DViewerView
)

router = DefaultRouter()
router.register(r'comparisons', ComparisonViewSet, basename='comparison')

app_name = 'projects'

urlpatterns = [
    # ==================== PUBLIC PROJECTS ====================
    path('', ProjectListView.as_view(), name='project-list'),
    path('<uuid:id>/', ProjectDetailView.as_view(), name='project-detail'),
    
    # ==================== DEVELOPER ENDPOINTS ====================
    path('create/', ProjectCreateView.as_view(), name='project-create'),
    path('<uuid:id>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('<uuid:id>/submit/', ProjectSubmitView.as_view(), name='project-submit'),
    path('developer/my/', DeveloperProjectsView.as_view(), name='developer-projects'),
    path('developer/dashboard/', DeveloperDashboardView.as_view(), name='developer-dashboard'),
    
    # ==================== ADMIN ENDPOINTS ====================
    path('admin/pending/', AdminPendingProjectsView.as_view(), name='admin-pending'),
    path('admin/<uuid:id>/review/', AdminProjectReviewView.as_view(), name='admin-review'),
    path('admin/<uuid:id>/archive/', AdminProjectArchiveView.as_view(), name='admin-archive'),
    path('admin/access-requests/', AdminAccessRequestsView.as_view(), name='admin-access-requests'),
    path('admin/access-requests/<uuid:id>/review/', RestrictedAccessReviewView.as_view(), name='access-review'),
    
    # ==================== INVESTOR ENDPOINTS ====================
    path('investor/dashboard/', InvestorDashboardView.as_view(), name='investor-dashboard'),
    
    # ==================== FAVORITES ====================
    path('favorites/', FavoriteListView.as_view(), name='favorites'),
    path('favorites/<uuid:project_id>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
    
    # ==================== COMPARISONS ====================
    path('', include(router.urls)),
    
    # ==================== RESTRICTED ACCESS ====================
    path('access/requests/', RestrictedAccessRequestView.as_view(), name='access-requests'),
    
    # ==================== MEDIA ====================
    path('<uuid:id>/media/upload/', ProjectMediaUploadView.as_view(), name='media-upload'),
    
    # ==================== 3D VIEWER ====================
    path('<uuid:id>/3d-viewer/', Project3DViewerView.as_view(), name='3d-viewer'),
    
    # ==================== STATISTICS ====================
    path('statistics/', ProjectStatisticsView.as_view(), name='statistics'),
]