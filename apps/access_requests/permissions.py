"""
Access Request Permissions - DRF Custom Permissions
SRS-based role and object-level permissions
"""

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied


class HasVerifiedInvestorAccess(permissions.BasePermission):
    """
    SRS 5.1: Only verified investors can request access
    """
    message = _('Email verification required to access this resource')
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_verified and
            request.user.is_investor
        )


class IsAccessRequestOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: Only request owner or admin can access
    """
    message = _('You do not have permission to access this request')
    
    def has_object_permission(self, request, view, obj):
        # Admin can access any request
        if request.user.is_admin:
            return True
        
        # Investor can access their own requests
        if request.user.is_investor and obj.investor == request.user:
            return True
        
        # Developer can access requests for their projects
        if request.user.is_developer and obj.project.developer == request.user:
            return True
        
        return False


class CanReviewAccessRequest(permissions.BasePermission):
    """
    SRS 5.7: Only admins can review (approve/reject/revoke) access requests
    """
    message = _('Only administrators can review access requests')
    
    def has_permission(self, request, view):
        if view.action in ['review', 'bulk_review', 'pending', 'stats']:
            return request.user.is_authenticated and request.user.is_admin
        return True
    
    def has_object_permission(self, request, view, obj):
        if view.action == 'review':
            return request.user.is_authenticated and request.user.is_admin
        return True


class HasProjectAccessIfRestricted(permissions.BasePermission):
    """
    SRS 5.7: Check if user has access to restricted project data
    Used in project serializers and views
    """
    message = _('Access to restricted project data requires approval')
    
    def has_object_permission(self, request, view, obj):
        # Public project data is always accessible
        if not hasattr(obj, 'has_restricted_data') or not obj.has_restricted_data:
            return True
        
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # Check if user has approved access request
        from .models import AccessRequest
        has_access = AccessRequest.objects.filter(
            investor=request.user,
            project=obj,
            status=AccessRequest.Status.APPROVED
        ).exists()
        
        return has_access


class CanCreateAccessRequest(permissions.BasePermission):
    """
    SRS 5.1 + 5.7: Validate access request creation
    """
    message = _('You cannot create an access request at this time')
    
    def has_permission(self, request, view):
        if view.action != 'create':
            return True
        
        # Must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Must be verified investor
        if not (request.user.is_verified and request.user.is_investor):
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # For create action, object permission is not applicable
        if view.action == 'create':
            return True
        
        return super().has_object_permission(request, view, obj)


class AccessRequestWorkflowPermission(permissions.BasePermission):
    """
    Workflow-based permissions for access request state changes
    """
    
    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update']:
            # Only pending requests can be updated by owner
            if obj.status != 'PENDING':
                return False
            
            # Only investor who created it can update while pending
            if obj.investor != request.user:
                return False
            
            return True
        
        if view.action == 'destroy':
            # Only pending requests can be deleted by owner
            # Admin can delete any request
            if request.user.is_admin:
                return True
            
            return obj.status == 'PENDING' and obj.investor == request.user
        
        return True