from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class to check if user is Admin.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'ADMIN'
        )


class IsDeveloper(BasePermission):
    """
    Permission class to check if user is Developer.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'DEVELOPER'
        )


class IsInvestor(BasePermission):
    """
    Permission class to check if user is Investor.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'INVESTOR'
        )


class IsEmailVerified(BasePermission):
    """
    Permission class to check if user has verified their email.
    SRS Requirement: Email verification required for certain actions.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_email_verified
        )


class IsProjectOwner(BasePermission):
    """
    Object-level permission to only allow owners of a project to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.developer == request.user