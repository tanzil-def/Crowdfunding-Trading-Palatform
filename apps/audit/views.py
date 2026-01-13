"""
Audit Views - Clean DRF Implementation
Read-only views for audit trail with comprehensive filtering
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
import csv
import json
from django.http import HttpResponse

from .models import AuditLog, SystemHealthLog
from .serializers import (
    AuditLogSerializer,
    AuditLogFilterSerializer,
    AuditLogSummarySerializer,
    SystemHealthLogSerializer,
    AuditExportSerializer
)
from apps.users.permissions import IsAdminUser
from utils.pagination import StandardResultsSetPagination


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for audit log access.
    Admin-only access to immutable audit trail.
    SRS Requirements: 5.12
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'action_category', 'target_model', 'actor']
    search_fields = ['description', 'metadata']
    ordering_fields = ['created_at', 'action_type']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Apply filters from query parameters"""
        queryset = super().get_queryset().select_related('actor')
        
        # Apply custom filters
        filter_serializer = AuditLogFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            
            if filters.get('target_id'):
                queryset = queryset.filter(target_id=filters['target_id'])
            
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get audit log summary statistics"""
        now = timezone.now()
        today = now.date()
        week_ago = now - timezone.timedelta(days=7)
        month_ago = now - timezone.timedelta(days=30)
        
        # Calculate statistics
        total_logs = AuditLog.objects.count()
        logs_today = AuditLog.objects.filter(created_at__date=today).count()
        logs_this_week = AuditLog.objects.filter(created_at__gte=week_ago).count()
        logs_this_month = AuditLog.objects.filter(created_at__gte=month_ago).count()
        
        # Group by category
        by_category = AuditLog.objects.values('action_category').annotate(
            count=Count('id')
        ).order_by('-count')
        by_category_dict = {item['action_category']: item['count'] for item in by_category}
        
        # Group by action type
        by_action_type = AuditLog.objects.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        by_action_type_dict = {item['action_type']: item['count'] for item in by_action_type}
        
        # Top actors
        top_actors = AuditLog.objects.exclude(actor__isnull=True).values(
            'actor__id', 'actor__email', 'actor__first_name', 'actor__last_name'
        ).annotate(
            action_count=Count('id')
        ).order_by('-action_count')[:10]
        
        # Recent actions
        recent_actions = AuditLog.objects.select_related('actor').order_by('-created_at')[:20]
        recent_actions_list = [
            {
                'id': str(log.id),
                'action_type': log.action_type,
                'actor_email': log.actor.email if log.actor else 'System',
                'target_model': log.target_model,
                'created_at': log.created_at
            }
            for log in recent_actions
        ]
        
        data = {
            'total_logs': total_logs,
            'logs_today': logs_today,
            'logs_this_week': logs_this_week,
            'logs_this_month': logs_this_month,
            'by_category': by_category_dict,
            'by_action_type': by_action_type_dict,
            'top_actors': list(top_actors),
            'recent_actions': recent_actions_list
        }
        
        serializer = AuditLogSummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_target(self, request):
        """Get audit logs for a specific target"""
        target_model = request.query_params.get('target_model')
        target_id = request.query_params.get('target_id')
        
        if not target_model or not target_id:
            return Response(
                {'error': _('target_model and target_id parameters required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                target_model=target_model,
                target_id=target_id
            )
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export audit logs in specified format"""
        serializer = AuditExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        export_format = serializer.validated_data['format']
        include_columns = serializer.validated_data['include_columns']
        filters = serializer.validated_data.get('filters', {})
        
        # Apply filters to queryset
        queryset = self.get_queryset()
        
        if filters.get('start_date'):
            queryset = queryset.filter(created_at__gte=filters['start_date'])
        
        if filters.get('end_date'):
            queryset = queryset.filter(created_at__lte=filters['end_date'])
        
        if filters.get('action_type'):
            queryset = queryset.filter(action_type=filters['action_type'])
        
        if filters.get('target_model'):
            queryset = queryset.filter(target_model=filters['target_model'])
        
        # Export based on format
        if export_format == 'csv':
            return self._export_csv(queryset, include_columns)
        elif export_format == 'json':
            return self._export_json(queryset, include_columns)
        else:
            return Response(
                {'error': _('Export format not supported')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def activity_timeline(self, request):
        """Get activity timeline data for charts"""
        days = int(request.query_params.get('days', 30))
        
        from django.db.models.functions import TruncDate
        
        timeline_data = AuditLog.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=days)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            admin_actions=Count('id', filter=Q(actor__role='ADMIN')),
            critical_actions=Count('id', filter=Q(action_category__in=['ACCESS_CONTROL', 'PAYMENT']))
        ).order_by('date')
        
        return Response(list(timeline_data))
    
    # Helper methods for export
    def _export_csv(self, queryset, include_columns):
        """Export audit logs as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.DictWriter(response, fieldnames=include_columns)
        writer.writeheader()
        
        for log in queryset:
            row = {}
            for column in include_columns:
                if column == 'actor':
                    row[column] = log.actor.email if log.actor else 'System'
                elif column == 'action_type':
                    row[column] = log.get_action_type_display()
                elif column == 'action_category':
                    row[column] = log.get_action_category_display()
                else:
                    row[column] = getattr(log, column, '')
            
            writer.writerow(row)
        
        return response
    
    def _export_json(self, queryset, include_columns):
        """Export audit logs as JSON"""
        data = []
        
        for log in queryset:
            entry = {}
            for column in include_columns:
                if column == 'actor':
                    entry[column] = {
                        'id': str(log.actor.id) if log.actor else None,
                        'email': log.actor.email if log.actor else 'System'
                    }
                elif column in ['action_type', 'action_category']:
                    entry[column] = getattr(log, f'get_{column}_display')()
                else:
                    value = getattr(log, column, '')
                    # Convert UUID to string
                    if isinstance(value, uuid.UUID):
                        value = str(value)
                    entry[column] = value
            
            data.append(entry)
        
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="audit_logs.json"'
        
        return response


class SystemHealthLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for system health monitoring logs.
    Admin-only access.
    """
    
    queryset = SystemHealthLog.objects.all()
    serializer_class = SystemHealthLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['component', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def current_status(self, request):
        """Get current system health status"""
        components = SystemHealthLog.objects.values('component').distinct()
        
        status_data = []
        for component in components:
            latest = SystemHealthLog.objects.filter(
                component=component['component']
            ).order_by('-created_at').first()
            
            if latest:
                status_data.append({
                    'component': component['component'],
                    'status': latest.status,
                    'last_checked': latest.created_at,
                    'message': latest.message,
                    'response_time_ms': latest.response_time_ms
                })
        
        return Response(status_data)
    
    @action(detail=False, methods=['get'])
    def health_summary(self, request):
        """Get system health summary"""
        total_checks = SystemHealthLog.objects.count()
        healthy_count = SystemHealthLog.objects.filter(status='HEALTHY').count()
        warning_count = SystemHealthLog.objects.filter(status='WARNING').count()
        error_count = SystemHealthLog.objects.filter(status='ERROR').count()
        critical_count = SystemHealthLog.objects.filter(status='CRITICAL').count()
        
        # Average response time for healthy components
        avg_response_time = SystemHealthLog.objects.filter(
            status='HEALTHY'
        ).aggregate(avg=models.Avg('response_time_ms'))['avg'] or 0
        
        # Components with recent errors
        recent_errors = SystemHealthLog.objects.filter(
            status__in=['ERROR', 'CRITICAL'],
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).values('component').annotate(
            error_count=Count('id')
        ).order_by('-error_count')[:10]
        
        return Response({
            'total_checks': total_checks,
            'healthy_count': healthy_count,
            'warning_count': warning_count,
            'error_count': error_count,
            'critical_count': critical_count,
            'health_percentage': (healthy_count / total_checks * 100) if total_checks > 0 else 0,
            'avg_response_time_ms': round(avg_response_time, 2),
            'recent_errors': list(recent_errors)
        })