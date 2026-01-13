from rest_framework.permissions import BasePermission


class IsDeveloper(BasePermission):
    """
    Permission check: User must be authenticated and have DEVELOPER role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'DEVELOPER'


class IsProjectOwner(BasePermission):
    """
    Object-level permission: User must be the project owner.
    """
    def has_object_permission(self, request, view, obj):
        return obj.developer == request.user


class IsAdmin(BasePermission):
    """
    Permission check: User must be authenticated and have ADMIN role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class IsInvestor(BasePermission):
    """
    Permission check: User must be authenticated and have INVESTOR role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'INVESTOR'


class CanViewRestrictedProject(BasePermission):
    """
    Check if user can view restricted project fields.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.role == 'ADMIN':
            return True
        
        if user == obj.developer:
            return True
        
        if user.role == 'INVESTOR':
            from apps.access_requests.models import AccessRequest
            return AccessRequest.objects.filter(
                investor=user,
                project=obj,
                status='APPROVED'
            ).exists()
        
        return False