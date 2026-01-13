"""
Audit Permissions - DRF Custom Permissions
Admin-only access with fine-grained control
"""

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsAuditAdmin(permissions.BasePermission):
    """
    SRS 5.12: Only admins can view audit logs
    """
    message = _('Only administrators can access audit logs')
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class CanExportAuditLogs(permissions.BasePermission):
    """
    Permission to export audit logs (additional security)
    """
    message = _('You do not have permission to export audit logs')
    
    def has_permission(self, request, view):
        if view.action == 'export':
            # Additional check: user must have export permission flag
            return (
                request.user.is_authenticated and
                request.user.is_admin and
                getattr(request.user, 'can_export_logs', True)
            )
        return True


class CanViewSystemHealth(permissions.BasePermission):
    """
    Permission to view system health logs
    """
    message = _('Only authorized administrators can view system health')
    
    def has_permission(self, request, view):
        if view.basename == 'system-health':
            return (
                request.user.is_authenticated and
                request.user.is_admin and
                getattr(request.user, 'can_view_system_health', True)
            )
        return True


class AuditLogFilterPermission(permissions.BasePermission):
    """
    Control which filters users can apply based on role
    """
    
    ALLOWED_FILTERS_FOR_ADMIN = [
        'action_type', 'action_category', 'target_model', 
        'target_id', 'actor', 'start_date', 'end_date'
    ]
    
    ALLOWED_FILTERS_FOR_DEVELOPER = [
        'target_model', 'target_id', 'start_date', 'end_date'
    ]
    
    def has_permission(self, request, view):
        # Check if user is trying to use restricted filters
        if request.method == 'GET' and 'audit' in request.path:
            filters = request.GET.keys()
            
            if request.user.is_admin:
                allowed_filters = self.ALLOWED_FILTERS_FOR_ADMIN
            elif request.user.is_developer:
                allowed_filters = self.ALLOWED_FILTERS_FOR_DEVELOPER
            else:
                allowed_filters = []
            
            # Check for any disallowed filters
            for filter_key in filters:
                if filter_key not in allowed_filters:
                    return False
        
        return True


class ImmutableAuditLogPermission(permissions.BasePermission):
    """
    Ensure audit logs cannot be modified (SRS: immutable logs)
    """
    message = _('Audit logs are immutable and cannot be modified')
    
    def has_permission(self, request, view):
        # Block any write operations on audit logs
        if view.basename == 'audit-log':
            if request.method not in permissions.SAFE_METHODS:
                return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Prevent any modifications to audit log entries
        if request.method not in permissions.SAFE_METHODS:
            return False
        return True


class CanViewAuditSummary(permissions.BasePermission):
    """
    Permission to view audit summary statistics
    """
    message = _('You do not have permission to view audit summary')
    
    def has_permission(self, request, view):
        if view.action in ['summary', 'activity_timeline', 'health_summary']:
            return (
                request.user.is_authenticated and
                request.user.is_admin
            )
        return True