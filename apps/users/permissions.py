from rest_framework import permissions


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission to check if user is verified
    SRS: Unverified investors cannot invest or request restricted access
    """
    
    message = 'Email verification required for this action.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_verified


class IsAdminUser(permissions.BasePermission):
    """
    Permission to check if user is admin
    """
    
    message = 'Admin access required.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_admin


class IsDeveloperUser(permissions.BasePermission):
    """
    Permission to check if user is developer
    """
    
    message = 'Developer access required.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_developer


class IsInvestorUser(permissions.BasePermission):
    """
    Permission to check if user is investor
    """
    
    message = 'Investor access required.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_investor


class CanInvest(permissions.BasePermission):
    """
    Combined permission for investment actions
    SRS: Must be verified investor and not banned
    """
    
    message = 'You must be a verified investor to invest.'
    
    def has_permission(self, request, view):
        user = request.user
        return (user and user.is_authenticated and 
                user.is_investor and user.is_verified and 
                user.is_active and not user.is_banned)


class CanCreateProject(permissions.BasePermission):
    """
    Permission for project creation
    SRS: Only developers can create projects
    """
    
    message = 'Only developers can create projects.'
    
    def has_permission(self, request, view):
        user = request.user
        return (user and user.is_authenticated and 
                user.is_developer and user.is_verified and 
                user.is_active and not user.is_banned)