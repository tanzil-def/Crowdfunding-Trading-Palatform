from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_developer

class IsInvestor(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_investor

class IsVerified(BasePermission):
    """For future: Block unverified investors from investing/access requests."""
    def has_permission(self, request, view):
        return request.user and request.user.is_verified