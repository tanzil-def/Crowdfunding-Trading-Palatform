from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Check if user is Admin"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsDeveloper(BasePermission):
    """Check if user is Developer"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'DEVELOPER'
        )


class IsInvestor(BasePermission):
    """Check if user is Investor"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'INVESTOR'
        )


class IsEmailVerified(BasePermission):
    """
    Check if user has verified email.
    SRS: Email verification required for certain actions.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_email_verified
        )