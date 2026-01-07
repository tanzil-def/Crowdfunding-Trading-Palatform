from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Only admins can access audit logs.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )
