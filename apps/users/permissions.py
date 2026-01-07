# apps/users/permissions.py

from rest_framework.permissions import BasePermission

<<<<<<< HEAD
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
=======

class IsVerified(BasePermission):
    """
    Allows access only to users with verified email.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_email_verified
        )


class IsRole(BasePermission):
    """
    Generic role-based permission.
    Pass a list of allowed roles when initializing.
    Example: IsRole(['DEVELOPER', 'INVESTOR'])
    """
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


# Specific roles for convenience and clarity
class IsAdmin(BasePermission):
    """
    Allows access only to ADMIN users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsDeveloper(BasePermission):
    """
    Allows access only to DEVELOPER users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'DEVELOPER'
        )


class IsInvestor(BasePermission):
    """
    Allows access only to INVESTOR users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'INVESTOR'
        )
>>>>>>> 83d38a9 (WIP: work in progress on project features)
