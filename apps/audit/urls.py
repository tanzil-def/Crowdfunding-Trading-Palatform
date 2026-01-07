from django.urls import path
from .views import AdminAuditLogListView

urlpatterns = [
    # Admin Audit Logs
    path('admin/audit-logs/', AdminAuditLogListView.as_view(), name='admin-audit-logs'),

]
