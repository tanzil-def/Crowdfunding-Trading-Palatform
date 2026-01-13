"""
Access Request Services - Business Logic Layer
Clean separation of concerns from views and models
"""

import uuid
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import AccessRequest, AccessRequestHistory
from apps.notifications.services import NotificationService
from apps.audit.services import AuditService


class AccessRequestService:
    """
    Service layer for access request business logic
    """
    
    @staticmethod
    def create_access_request(
        investor,
        project,
        purpose: str = '',
        requested_fields: List[str] = None
    ) -> AccessRequest:
        """
        Create a new access request with validation
        SRS: Verified investors can request access
        """
        # Validation
        if not investor.is_verified:
            raise ValidationError(_('Email verification required'))
        
        if not investor.is_investor:
            raise ValidationError(_('Only investors can request access'))
        
        if project.status != 'APPROVED':
            raise ValidationError(_('Can only request access to approved projects'))
        
        # Check for existing active request
        existing = AccessRequest.objects.filter(
            investor=investor,
            project=project,
            status__in=[AccessRequest.Status.PENDING, AccessRequest.Status.APPROVED]
        ).exists()
        
        if existing:
            raise ValidationError(_('You already have an active access request'))
        
        # Create request
        with transaction.atomic():
            access_request = AccessRequest.objects.create(
                investor=investor,
                project=project,
                purpose=purpose,
                requested_fields=requested_fields or []
            )
            
            # Create history entry
            AccessRequestHistory.objects.create(
                access_request=access_request,
                previous_status='',
                new_status=AccessRequest.Status.PENDING,
                changed_by=investor,
                notes='Access request created'
            )
        
        return access_request
    
    @staticmethod
    def approve_request(
        access_request: AccessRequest,
        reviewer,
        notes: str = ''
    ) -> AccessRequest:
        """
        Approve access request
        SRS: Admin can approve access
        """
        if access_request.status != AccessRequest.Status.PENDING:
            raise ValidationError(_('Only pending requests can be approved'))
        
        with transaction.atomic():
            access_request.approve(reviewer, notes)
            
            # Create audit log
            AuditService.log_access_request(
                action_type='ACCESS_APPROVED',
                actor=reviewer,
                access_request=access_request,
                metadata={
                    'notes': notes,
                    'investor_email': access_request.investor.email,
                    'project_title': access_request.project.title
                }
            )
            
            # Send notification
            NotificationService.send_access_request_approved(
                access_request=access_request,
                reviewer=reviewer
            )
        
        return access_request
    
    @staticmethod
    def reject_request(
        access_request: AccessRequest,
        reviewer,
        notes: str = ''
    ) -> AccessRequest:
        """
        Reject access request
        SRS: Admin can reject access
        """
        if access_request.status != AccessRequest.Status.PENDING:
            raise ValidationError(_('Only pending requests can be rejected'))
        
        with transaction.atomic():
            access_request.reject(reviewer, notes)
            
            # Create audit log
            AuditService.log_access_request(
                action_type='ACCESS_REJECTED',
                actor=reviewer,
                access_request=access_request,
                metadata={
                    'notes': notes,
                    'investor_email': access_request.investor.email,
                    'project_title': access_request.project.title
                }
            )
            
            # Send notification
            NotificationService.send_access_request_rejected(
                access_request=access_request,
                reviewer=reviewer
            )
        
        return access_request
    
    @staticmethod
    def revoke_access(
        access_request: AccessRequest,
        reviewer,
        notes: str = ''
    ) -> AccessRequest:
        """
        Revoke access immediately
        SRS: Immediate revocation
        """
        if access_request.status != AccessRequest.Status.APPROVED:
            raise ValidationError(_('Only approved access can be revoked'))
        
        with transaction.atomic():
            access_request.revoke(reviewer, notes)
            
            # Create audit log
            AuditService.log_access_request(
                action_type='ACCESS_REVOKED',
                actor=reviewer,
                access_request=access_request,
                metadata={
                    'notes': notes,
                    'investor_email': access_request.investor.email,
                    'project_title': access_request.project.title
                }
            )
            
            # Send notification
            NotificationService.send_access_revoked(
                access_request=access_request,
                reviewer=reviewer
            )
        
        return access_request
    
    @staticmethod
    def get_pending_requests_count() -> int:
        """Get count of pending requests for admin dashboard"""
        return AccessRequest.objects.filter(
            status=AccessRequest.Status.PENDING
        ).count()
    
    @staticmethod
    def get_investor_access_status(investor, project) -> Dict:
        """
        Check if investor has access to project's restricted data
        Returns access status and details
        """
        try:
            access_request = AccessRequest.objects.get(
                investor=investor,
                project=project
            )
            
            return {
                'has_access': access_request.has_access,
                'status': access_request.status,
                'request_id': str(access_request.id),
                'requested_at': access_request.created_at,
                'reviewed_at': access_request.reviewed_at,
                'review_notes': access_request.review_notes
            }
        except AccessRequest.DoesNotExist:
            return {
                'has_access': False,
                'status': 'NO_REQUEST',
                'message': 'No access request found'
            }
    
    @staticmethod
    def get_access_request_stats() -> Dict:
        """
        Get statistics for admin dashboard
        """
        from django.db.models import Count, Q, Avg
        from django.db.models.functions import TruncDate
        
        # Basic counts
        total = AccessRequest.objects.count()
        pending = AccessRequest.objects.filter(
            status=AccessRequest.Status.PENDING
        ).count()
        
        # Approval rate
        reviewed = AccessRequest.objects.filter(
            status__in=['APPROVED', 'REJECTED']
        ).count()
        
        approval_rate = 0
        if reviewed > 0:
            approved = AccessRequest.objects.filter(
                status='APPROVED'
            ).count()
            approval_rate = (approved / reviewed) * 100
        
        # Average processing time
        processed = AccessRequest.objects.filter(
            reviewed_at__isnull=False
        ).annotate(
            processing_time=timezone.now() - models.F('created_at')
        )
        
        avg_processing_hours = 0
        if processed.exists():
            avg_seconds = processed.aggregate(
                avg=Avg('processing_time')
            )['avg'].total_seconds()
            avg_processing_hours = avg_seconds / 3600
        
        # Daily trends
        daily_stats = AccessRequest.objects.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')[:7]
        
        return {
            'total_requests': total,
            'pending_requests': pending,
            'approval_rate': round(approval_rate, 2),
            'avg_processing_hours': round(avg_processing_hours, 2),
            'daily_trends': list(daily_stats)
        }
    
    @staticmethod
    def bulk_review_requests(
        request_ids: List[uuid.UUID],
        action: str,
        reviewer,
        notes: str = ''
    ) -> List[Dict]:
        """
        Process multiple access requests in bulk
        Returns list of results with status for each
        """
        results = []
        
        for request_id in request_ids:
            try:
                access_request = AccessRequest.objects.get(id=request_id)
                
                # Perform action based on current status
                if action == 'approve' and access_request.status == 'PENDING':
                    AccessRequestService.approve_request(access_request, reviewer, notes)
                    result_status = 'APPROVED'
                elif action == 'reject' and access_request.status == 'PENDING':
                    AccessRequestService.reject_request(access_request, reviewer, notes)
                    result_status = 'REJECTED'
                else:
                    result_status = 'SKIPPED'
                
                results.append({
                    'request_id': str(request_id),
                    'status': 'SUCCESS',
                    'action': action,
                    'new_status': result_status
                })
                
            except AccessRequest.DoesNotExist:
                results.append({
                    'request_id': str(request_id),
                    'status': 'ERROR',
                    'message': 'Access request not found'
                })
            except ValidationError as e:
                results.append({
                    'request_id': str(request_id),
                    'status': 'ERROR',
                    'message': str(e)
                })
        
        return results


class AccessRequestValidator:
    """
    Validation service for access requests
    """
    
    @staticmethod
    def validate_investor_can_request(investor) -> Tuple[bool, str]:
        """Check if investor can make access request"""
        if not investor.is_verified:
            return False, 'Email verification required'
        
        if not investor.is_investor:
            return False, 'Only investors can request access'
        
        return True, ''
    
    @staticmethod
    def validate_project_for_access(project) -> Tuple[bool, str]:
        """Check if project can receive access requests"""
        if project.status != 'APPROVED':
            return False, 'Project must be approved'
        
        if not project.has_restricted_data:
            return False, 'Project has no restricted data'
        
        return True, ''
    
    @staticmethod
    def check_duplicate_request(investor, project) -> Tuple[bool, str]:
        """Check for duplicate active request"""
        exists = AccessRequest.objects.filter(
            investor=investor,
            project=project,
            status__in=['PENDING', 'APPROVED']
        ).exists()
        
        if exists:
            return True, 'You already have an active access request'
        
        return False, ''