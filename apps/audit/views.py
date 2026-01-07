from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.audit.permissions import IsAdmin

class AdminAuditLogListView(generics.ListAPIView):
    """
    GET /admin/audit-logs/
    Admin-only view to list all audit logs.
    Supports pagination.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    # Optional: add filters for entity_type, actor, or date range in future
