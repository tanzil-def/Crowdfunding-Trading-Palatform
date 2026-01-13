"""
Investment Permissions
Production-ready permission classes for investment workflow
"""

from rest_framework import permissions


class IsInvestorOwner(permissions.BasePermission):
    """
    Permission: User must be the owner of the investment
    Used for: cancel, update, view own investments
    """
    
    message = 'You do not own this investment'
    
    def has_object_permission(self, request, view, obj):
        return obj.investor == request.user


class IsAdminUser(permissions.BasePermission):
    """
    Permission: User must be an admin
    Used for: review, approve/reject, system-wide stats
    """
    
    message = 'Admin access required'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_staff)
        )


class IsVerifiedInvestor(permissions.BasePermission):
    """
    Permission: User must be a verified investor
    Used for: create investment, initiate payment
    SRS: Email verification required before investing
    """
    
    message = 'Verified investor access required'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_investor and
            request.user.is_verified and
            not request.user.is_banned
        )


class CanReviewInvestment(permissions.BasePermission):
    """
    Permission: User can review investments (admin only)
    Used for: approve/reject investment requests
    """
    
    message = 'Only admins can review investments'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_staff)
        )
    
    def has_object_permission(self, request, view, obj):
        if not (request.user.is_admin or request.user.is_staff):
            return False
        
        if obj.status not in ['REQUESTED', 'APPROVED']:
            self.message = 'Investment cannot be reviewed in current status'
            return False
        
        return True


class CanInitiatePayment(permissions.BasePermission):
    """
    Permission: User can initiate payment for their approved investment
    Used for: payment processing
    """
    
    message = 'Cannot initiate payment for this investment'
    
    def has_object_permission(self, request, view, obj):
        if obj.investor != request.user:
            self.message = 'You do not own this investment'
            return False
        
        if obj.status != 'APPROVED':
            self.message = 'Investment must be approved before payment'
            return False
        
        if obj.is_expired:
            self.message = 'Investment approval has expired'
            return False
        
        return True


class CanCancelInvestment(permissions.BasePermission):
    """
    Permission: User can cancel their own investment
    Used for: investment cancellation
    """
    
    message = 'Cannot cancel this investment'
    
    def has_object_permission(self, request, view, obj):
        if obj.investor != request.user:
            self.message = 'You do not own this investment'
            return False
        
        if obj.status not in ['REQUESTED', 'APPROVED']:
            self.message = f'Cannot cancel investment in {obj.status} status'
            return False
        
        return True


class CanViewInvestment(permissions.BasePermission):
    """
    Permission: User can view investment details
    Used for: retrieve investment
    """
    
    message = 'You do not have permission to view this investment'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.is_admin or user.is_staff:
            return True
        
        if obj.investor == user:
            return True
        
        if hasattr(obj.project, 'developer') and obj.project.developer == user:
            return True
        
        return False