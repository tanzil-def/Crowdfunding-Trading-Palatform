"""
Access Request ViewSet - Clean DRF Implementation
Complete access control workflow with proper permissions
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Avg
from django.utils import timezone

from .models import AccessRequest, AccessRequestHistory
from .serializers import (
    AccessRequestSerializer,
    AccessRequestCreateSerializer,
    AccessRequestReviewSerializer,
    AccessRequestHistorySerializer,
    AccessRequestStatsSerializer
)
from apps.users.permissions import IsAdminUser, IsVerifiedInvestor
from utils.pagination import StandardResultsSetPagination
from utils.permissions import IsObjectOwnerOrAdmin, IsDeveloperOfProject


class AccessRequestViewSet(viewsets.ModelViewSet):
    """
    Complete ViewSet for access request management.
    SRS Requirements: 5.1, 5.3, 5.4, 5.7, 5.10, 5.12
    """
    
    queryset = AccessRequest.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project', 'investor']
    search_fields = [
        'project__title',
        'investor__email',
        'investor__first_name',
        'investor__last_name',
        'purpose'
    ]
    ordering_fields = ['created_at', 'reviewed_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        serializer_map = {
            'create': AccessRequestCreateSerializer,
            'review': AccessRequestReviewSerializer,
            'stats': AccessRequestStatsSerializer,
            'history': AccessRequestHistorySerializer,
        }
        return serializer_map.get(self.action, AccessRequestSerializer)
    
    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsVerifiedInvestor()]
        elif self.action in ['review', 'pending', 'stats', 'bulk_review']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsObjectOwnerOrAdmin()]
        elif self.action in ['my_requests', 'check_access']:
            return [permissions.IsAuthenticated(), IsVerifiedInvestor()]
        else:
            return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """Role-based queryset filtering"""
        user = self.request.user
        
        if not user.is_authenticated:
            return AccessRequest.objects.none()
        
        queryset = super().get_queryset().select_related(
            'investor', 'project', 'reviewed_by'
        )
        
        if user.is_admin:
            return queryset
        
        if user.is_investor:
            return queryset.filter(investor=user)
        
        if user.is_developer:
            # Developers can see requests for their projects
            return queryset.filter(project__developer=user)
        
        return AccessRequest.objects.none()
    
    def perform_create(self, serializer):
        """Create access request with notifications"""
        access_request = serializer.save()
        
        # Create initial history entry
        AccessRequestHistory.objects.create(
            access_request=access_request,
            previous_status='',
            new_status=AccessRequest.Status.PENDING,
            changed_by=self.request.user,
            notes='Access request created'
        )
        
        # Send notifications
        self._send_notifications(access_request, 'created')
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's access requests"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(investor=request.user)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Admin: Get all pending requests"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=AccessRequest.Status.PENDING)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Admin: Review access request"""
        access_request = self.get_object()
        serializer = AccessRequestReviewSerializer(
            instance=access_request,
            data=request.data
        )
        
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        # Perform action
        if action == 'approve':
            access_request.approve(request.user, notes)
        elif action == 'reject':
            access_request.reject(request.user, notes)
        elif action == 'revoke':
            access_request.revoke(request.user, notes)
        
        # Send notifications
        self._send_notifications(access_request, action)
        
        # Create audit log
        self._log_audit_action(access_request, action)
        
        return Response(
            AccessRequestSerializer(access_request).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def bulk_review(self, request):
        """Admin: Bulk review multiple requests"""
        request_ids = request.data.get('request_ids', [])
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if not request_ids or not action:
            raise ValidationError({
                'request_ids': _('List of request IDs required'),
                'action': _('Action required')
            })
        
        results = []
        for request_id in request_ids:
            try:
                access_request = AccessRequest.objects.get(
                    id=request_id,
                    status=AccessRequest.Status.PENDING
                )
                
                if action == 'approve':
                    access_request.approve(request.user, notes)
                elif action == 'reject':
                    access_request.reject(request.user, notes)
                
                results.append({
                    'id': str(request_id),
                    'status': 'success',
                    'new_status': access_request.status
                })
                
                self._send_notifications(access_request, action)
                self._log_audit_action(access_request, action)
                
            except AccessRequest.DoesNotExist:
                results.append({
                    'id': str(request_id),
                    'status': 'error',
                    'message': _('Request not found or not pending')
                })
        
        return Response({'results': results}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get audit history for access request"""
        access_request = self.get_object()
        history = AccessRequestHistory.objects.filter(
            access_request=access_request
        ).select_related('changed_by').order_by('-changed_at')
        
        serializer = AccessRequestHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Admin: Get access request statistics"""
        from django.db.models.functions import TruncDate
        
        # Calculate statistics
        total_requests = AccessRequest.objects.count()
        pending_requests = AccessRequest.objects.filter(
            status=AccessRequest.Status.PENDING
        ).count()
        
        approved_today = AccessRequest.objects.filter(
            status=AccessRequest.Status.APPROVED,
            reviewed_at__date=timezone.now().date()
        ).count()
        
        # Approval rate
        reviewed_count = AccessRequest.objects.filter(
            status__in=[AccessRequest.Status.APPROVED, AccessRequest.Status.REJECTED]
        ).count()
        
        approval_rate = 0
        if reviewed_count > 0:
            approved_count = AccessRequest.objects.filter(
                status=AccessRequest.Status.APPROVED
            ).count()
            approval_rate = (approved_count / reviewed_count) * 100
        
        # Average processing time (in hours)
        processed_requests = AccessRequest.objects.filter(
            reviewed_at__isnull=False
        ).annotate(
            processing_time=models.ExpressionWrapper(
                models.F('reviewed_at') - models.F('created_at'),
                output_field=models.DurationField()
            )
        )
        
        avg_processing_time = 0
        if processed_requests.exists():
            avg_seconds = processed_requests.aggregate(
                avg=models.Avg('processing_time')
            )['avg'].total_seconds()
            avg_processing_time = avg_seconds / 3600  # Convert to hours
        
        # Top projects by requests
        top_projects = AccessRequest.objects.values(
            'project__title', 'project_id'
        ).annotate(
            total_requests=Count('id'),
            approved_requests=Count('id', filter=Q(status=AccessRequest.Status.APPROVED))
        ).order_by('-total_requests')[:10]
        
        # Status distribution
        status_distribution = AccessRequest.objects.values(
            'status'
        ).annotate(
            count=Count('id')
        ).order_by('status')
        
        data = {
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_today': approved_today,
            'approval_rate': round(approval_rate, 2),
            'avg_processing_time_hours': round(avg_processing_time, 2),
            'top_projects': list(top_projects),
            'status_distribution': {item['status']: item['count'] for item in status_distribution}
        }
        
        serializer = AccessRequestStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def check_access(self, request):
        """Check if user has access to specific project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            raise ValidationError({'project_id': _('Project ID required')})
        
        try:
            access_request = AccessRequest.objects.get(
                investor=request.user,
                project_id=project_id,
                status=AccessRequest.Status.APPROVED
            )
            return Response({
                'has_access': True,
                'access_request_id': str(access_request.id),
                'granted_at': access_request.reviewed_at,
                'review_notes': access_request.review_notes
            })
        except AccessRequest.DoesNotExist:
            return Response({
                'has_access': False,
                'message': _('No approved access request found')
            })
    
    # Helper Methods
    def _send_notifications(self, access_request, action):
        """Send notifications for access request actions"""
        try:
            from apps.notifications.services import NotificationService
            
            if action == 'created':
                # Notify admins
                NotificationService.notify_admins(
                    notification_type='ACCESS_REQUEST_CREATED',
                    title='New Access Request',
                    message=f'{access_request.investor.email} requested access to {access_request.project.title}',
                    related_object=access_request
                )
            else:
                # Notify investor
                NotificationService.notify_user(
                    user=access_request.investor,
                    notification_type=f'ACCESS_REQUEST_{action.upper()}',
                    title=f'Access Request {action.capitalize()}',
                    message=f'Your access request for {access_request.project.title} has been {action}',
                    related_object=access_request
                )
        except ImportError:
            # Notifications app not available
            pass
    
    def _log_audit_action(self, access_request, action):
        """Log action to audit system"""
        try:
            from apps.audit.services import AuditService
            
            AuditService.log_access_request(
                action_type=f'ACCESS_REQUEST_{action.upper()}',
                actor=self.request.user,
                access_request=access_request,
                metadata={
                    'investor_email': access_request.investor.email,
                    'project_title': access_request.project.title
                }
            )
        except ImportError:
            # Audit app not available
            pass