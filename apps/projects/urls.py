from django.urls import path
from .views import (
    ProjectCreateView,
    MyProjectListView,
    ProjectUpdateView,
    ProjectSubmitView,
    ProjectMediaUploadView,
    ProjectMediaListView,
    AdminPendingProjectListView,
    AdminProjectApproveView,
    AdminProjectRejectView,
    AdminProjectRequestChangesView,
    InvestorProjectBrowseView,
    InvestorProjectCompareView,
    InvestorProjectDetailView,
)

urlpatterns = [
    # Developer - Project Management
    path('', ProjectCreateView.as_view(), name='project-create'),
    path('my/', MyProjectListView.as_view(), name='my-projects'),
    path('<uuid:id>/', ProjectUpdateView.as_view(), name='project-update'),
    path('<uuid:id>/submit/', ProjectSubmitView.as_view(), name='project-submit'),
    
    # Developer - Project Media
    path('<uuid:id>/media/', ProjectMediaUploadView.as_view(), name='project-media-upload'),
    path('<uuid:id>/media/list/', ProjectMediaListView.as_view(), name='project-media-list'),
    
    # Admin - Project Review
    path('admin/projects/pending/', AdminPendingProjectListView.as_view(), name='admin-pending-projects'),
    path('admin/projects/<uuid:id>/approve/', AdminProjectApproveView.as_view(), name='admin-approve-project'),
    path('admin/projects/<uuid:id>/reject/', AdminProjectRejectView.as_view(), name='admin-reject-project'),
    path('admin/projects/<uuid:id>/request-changes/', AdminProjectRequestChangesView.as_view(), name='admin-request-changes'),
    
    # Investor - Project Discovery
    path('browse/', InvestorProjectBrowseView.as_view(), name='investor-browse-projects'),
    path('compare/', InvestorProjectCompareView.as_view(), name='investor-compare-projects'),
    path('<uuid:id>/detail/', InvestorProjectDetailView.as_view(), name='investor-project-detail'),
]