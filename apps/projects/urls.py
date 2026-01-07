from django.urls import path
from .views import (
    # Phase 2 – Developer Project
    ProjectCreateView,
    MyProjectListView,
    ProjectUpdateView,
    ProjectSubmitView,

    # Phase 3 – Project Media
    ProjectMediaUploadView,
    ProjectMediaListView,

    # Phase 4 – Admin Review
    AdminPendingProjectListView,
    AdminProjectApproveView,
    AdminProjectRejectView,
    AdminProjectRequestChangesView,

    # Phase 5 – Investor Browse / Compare
    InvestorProjectBrowseView,
    InvestorProjectCompareView,
    InvestorProjectDetailView,
)

urlpatterns = [
    # ===============================
    # Phase 2 – Developer Project
    # ===============================
    path('', ProjectCreateView.as_view(), name='project-create'),
    path('my/', MyProjectListView.as_view(), name='my-projects'),
    path('<uuid:id>/', ProjectUpdateView.as_view(), name='project-update'),
    path('<uuid:id>/submit/', ProjectSubmitView.as_view(), name='project-submit'),

    # ===============================
    # Phase 3 – Project Media
    # ===============================
    path('<uuid:id>/media/', ProjectMediaUploadView.as_view(), name='project-media-upload'),
    path('<uuid:id>/media/list/', ProjectMediaListView.as_view(), name='project-media-list'),

    # ===============================
    # Phase 4 – Admin Review
    # ===============================
    path('admin/projects/pending/', AdminPendingProjectListView.as_view(), name='admin-project-pending'),
    path('admin/projects/<uuid:id>/approve/', AdminProjectApproveView.as_view(), name='admin-project-approve'),
    path('admin/projects/<uuid:id>/reject/', AdminProjectRejectView.as_view(), name='admin-project-reject'),
    path('admin/projects/<uuid:id>/request-changes/', AdminProjectRequestChangesView.as_view(), name='admin-project-request-changes'),

    # ===============================
    # Phase 5 – Investor Browse / Compare
    # ===============================
    path('browse/', InvestorProjectBrowseView.as_view(), name='investor-project-browse'),
    path('compare/', InvestorProjectCompareView.as_view(), name='investor-project-compare'),
    path('<uuid:id>/detail/', InvestorProjectDetailView.as_view(), name='investor-project-detail'),
]
