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
    queryset = AuditLog.objects.all().select_related('actor')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['action', 'entity_type', 'actor']
    search_fields = ['action', 'entity_type', 'metadata', 'actor__email']
    ordering_fields = ['created_at']
