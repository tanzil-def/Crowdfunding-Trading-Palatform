from django.urls import path
from .views import (
    AccessRequestCreateView,
    MyAccessRequestListView,
    AdminAccessRequestApproveView,
    AdminAccessRequestRejectView,
    AdminAccessRequestRevokeView
)

urlpatterns = [
    path('', AccessRequestCreateView.as_view(), name='access-request-create'),
    path('my/', MyAccessRequestListView.as_view(), name='access-request-my'),
    path('admin/<uuid:id>/approve/', AdminAccessRequestApproveView.as_view(), name='access-request-approve'),
    path('admin/<uuid:id>/reject/', AdminAccessRequestRejectView.as_view(), name='access-request-reject'),
    path('admin/<uuid:id>/revoke/', AdminAccessRequestRevokeView.as_view(), name='access-request-revoke'),
]
