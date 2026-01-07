from rest_framework.permissions import BasePermission

class IsInvestor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == 'INVESTOR')

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == 'ADMIN')

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.investor == request.user or request.user.role == 'ADMIN'
