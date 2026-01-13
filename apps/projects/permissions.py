from rest_framework import permissions
from .models import Project, RestrictedAccessRequest


class IsProjectDeveloper(permissions.BasePermission):
    """Check if user is the project developer"""
    
    def has_object_permission(self, request, view, obj):
        return obj.developer == request.user


class CanEditProject(permissions.BasePermission):
    """Check if user can edit project based on status"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user == obj.developer:
            return False
        
        # SRS: Developers can edit only in allowed states
        return obj.status in [Project.Status.DRAFT, Project.Status.NEEDS_CHANGES]


class CanSubmitProject(permissions.BasePermission):
    """Check if user can submit project for review"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user == obj.developer:
            return False
        
        # SRS: Only draft projects can be submitted
        return obj.status == Project.Status.DRAFT


class CanViewRestrictedData(permissions.BasePermission):
    """Check if user can view restricted project data"""
    
    def has_object_permission(self, request, view, obj):
        # Allow safe methods for non-restricted data
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins and developers have full access
        if request.user.is_admin or request.user == obj.developer:
            return True
        
        # Investors need approved access
        if request.user.is_investor:
            return RestrictedAccessRequest.objects.filter(
                investor=request.user,
                project=obj,
                status=RestrictedAccessRequest.Status.APPROVED
            ).exists()
        
        return False


class CanCompareProjects(permissions.BasePermission):
    """Check if user can compare projects"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # SRS: Only investors can compare projects
        return request.user.is_investor and request.user.is_verified


class CanFavoriteProject(permissions.BasePermission):
    """Check if user can favorite a project"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # SRS: Only verified investors can favorite
        return request.user.is_investor and request.user.is_verified
    
    def has_object_permission(self, request, view, obj):
        # Check if project is approved (SRS: Only approved projects in favorites)
        return obj.status == Project.Status.APPROVED


class CanRequestAccess(permissions.BasePermission):
    """Check if user can request access to restricted data"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # SRS: Verified investors can request access
        return request.user.is_investor and request.user.is_verified