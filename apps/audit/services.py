"""
Audit Services - Business Logic Layer
Centralized logging and audit trail management
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDate, TruncHour
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from .models import AuditLog, SystemHealthLog
from apps.users.models import User


class AuditService:
    """
    Central service for audit logging operations
    SRS: All critical actions must be logged
    """
    
    @staticmethod
    @transaction.atomic
    def log_action(
        action_type: str,
        actor,
        target_model: str,
        target_id: uuid.UUID,
        description: str = '',
        metadata: Dict = None,
        request = None
    ) -> AuditLog:
        """
        Generic method to log any action
        """
        # Get IP and user agent from request if available
        actor_ip = None
        actor_user_agent = ''
        
        if request:
            actor_ip = request.META.get('REMOTE_ADDR')
            actor_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Determine action category based on action type
        action_category = AuditService._determine_action_category(action_type)
        
        # Create audit log entry
        audit_log = AuditLog.objects.create(
            action_category=action_category,
            action_type=action_type,
            actor=actor,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            target_model=target_model,
            target_id=target_id,
            description=description,
            metadata=metadata or {}
        )
        
        # Update cache for quick stats
        AuditService._update_audit_cache()
        
        return audit_log
    
    @staticmethod
    def log_access_request(
        action_type: str,
        actor,
        access_request,
        metadata: Dict = None
    ) -> AuditLog:
        """
        Log access request actions
        SRS: All access decisions shall be logged
        """
        description = (
            f"Access request for project '{access_request.project.title}' "
            f"by investor {access_request.investor.email} - {action_type}"
        )
        
        return AuditService.log_action(
            action_type=action_type,
            actor=actor,
            target_model='AccessRequest',
            target_id=access_request.id,
            description=description,
            metadata=metadata or {}
        )
    
    @staticmethod
    def log_payment(
        action_type: str,
        actor,
        payment,
        metadata: Dict = None
    ) -> AuditLog:
        """
        Log payment actions
        SRS: Payment success/failure events shall be logged
        """
        description = (
            f"Payment {action_type} - Amount: {metadata.get('amount', 'N/A')} "
            f"for investment {payment.investment_id}"
        )
        
        return AuditService.log_action(
            action_type=action_type,
            actor=actor,
            target_model='PaymentTransaction',
            target_id=payment.id,
            description=description,
            metadata=metadata or {}
        )
    
    @staticmethod
    def log_project_action(
        action_type: str,
        actor,
        project,
        metadata: Dict = None
    ) -> AuditLog:
        """
        Log project-related actions
        """
        description = f"Project '{project.title}' - {action_type}"
        
        return AuditService.log_action(
            action_type=action_type,
            actor=actor,
            target_model='Project',
            target_id=project.id,
            description=description,
            metadata=metadata or {}
        )
    
    @staticmethod
    def log_user_action(
        action_type: str,
        actor,
        user,
        metadata: Dict = None
    ) -> AuditLog:
        """
        Log user-related actions
        """
        description = f"User {user.email} - {action_type}"
        
        return AuditService.log_action(
            action_type=action_type,
            actor=actor,
            target_model='User',
            target_id=user.id,
            description=description,
            metadata=metadata or {}
        )
    
    @staticmethod
    def get_audit_summary(days: int = 30) -> Dict:
        """
        Get comprehensive audit summary for dashboard
        """
        cache_key = f'audit_summary_{days}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get logs in date range
        logs = AuditLog.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        # Total counts
        total_logs = logs.count()
        
        # By action category
        by_category = logs.values('action_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # By action type (top 10)
        by_action_type = logs.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Top actors
        top_actors = logs.exclude(actor__isnull=True).values(
            'actor__email', 'actor__first_name', 'actor__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Daily activity
        daily_activity = logs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Critical actions (ACCESS_CONTROL, PAYMENT)
        critical_actions = logs.filter(
            action_category__in=['ACCESS_CONTROL', 'PAYMENT']
        ).count()
        
        summary = {
            'total_logs': total_logs,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            },
            'by_category': list(by_category),
            'by_action_type': list(by_action_type),
            'top_actors': list(top_actors),
            'daily_activity': list(daily_activity),
            'critical_actions': critical_actions,
            'critical_percentage': (critical_actions / total_logs * 100) if total_logs > 0 else 0
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, summary, 300)
        
        return summary
    
    @staticmethod
    def get_activity_timeline(days: int = 7) -> List[Dict]:
        """
        Get activity timeline for charts
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        timeline = AuditLog.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('created_at'),
            hour=TruncHour('created_at')
        ).values('date', 'hour').annotate(
            total=Count('id'),
            admin_actions=Count('id', filter=Q(actor__role='ADMIN')),
            critical_actions=Count('id', filter=Q(action_category__in=['ACCESS_CONTROL', 'PAYMENT']))
        ).order_by('date', 'hour')
        
        return list(timeline)
    
    @staticmethod
    def export_audit_logs(
        format: str = 'csv',
        filters: Dict = None,
        include_columns: List[str] = None
    ) -> Any:
        """
        Export audit logs in specified format
        """
        # Apply filters
        queryset = AuditLog.objects.all()
        
        if filters:
            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])
            if filters.get('action_type'):
                queryset = queryset.filter(action_type=filters['action_type'])
            if filters.get('target_model'):
                queryset = queryset.filter(target_model=filters['target_model'])
        
        # Default columns
        if not include_columns:
            include_columns = [
                'action_type', 'action_category', 
                'actor__email', 'target_model', 
                'target_id', 'created_at'
            ]
        
        # Prepare data based on format
        if format == 'json':
            data = list(queryset.values(*include_columns))
            return json.dumps(data, indent=2, default=str)
        
        elif format == 'csv':
            # Convert to CSV format
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(include_columns)
            
            # Write data
            for log in queryset:
                row = []
                for column in include_columns:
                    value = AuditService._get_nested_attribute(log, column)
                    row.append(str(value) if value else '')
                writer.writerow(row)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def search_audit_logs(
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Full-text search in audit logs
        """
        from django.db.models import Value as V
        from django.db.models.functions import Concat
        
        # Search in description, metadata, and actor email
        logs = AuditLog.objects.annotate(
            search_text=Concat(
                'description', V(' '),
                'actor__email', V(' '),
                'target_model', V(' ')
            )
        ).filter(
            Q(description__icontains=query) |
            Q(actor__email__icontains=query) |
            Q(target_model__icontains=query) |
            Q(metadata__icontains=query)
        ).order_by('-created_at')
        
        total = logs.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            'query': query,
            'total_results': total,
            'page': page,
            'page_size': page_size,
            'results': list(logs[start:end].values(
                'id', 'action_type', 'description',
                'actor__email', 'target_model',
                'target_id', 'created_at'
            ))
        }
    
    # Helper methods
    @staticmethod
    def _determine_action_category(action_type: str) -> str:
        """Map action type to category"""
        category_map = {
            'ACCESS_': 'ACCESS_CONTROL',
            'PROJECT_': 'PROJECT',
            'PAYMENT_': 'PAYMENT',
            'USER_': 'USER',
            'LOGIN': 'AUTHENTICATION',
            'LOGOUT': 'AUTHENTICATION',
            'PASSWORD_': 'AUTHENTICATION'
        }
        
        for prefix, category in category_map.items():
            if action_type.startswith(prefix):
                return category
        
        return 'SYSTEM'
    
    @staticmethod
    def _get_nested_attribute(obj, attr_path: str):
        """Get nested attribute using dot notation"""
        value = obj
        for attr in attr_path.split('__'):
            if hasattr(value, attr):
                value = getattr(value, attr)
            elif isinstance(value, dict) and attr in value:
                value = value[attr]
            else:
                return None
        return value
    
    @staticmethod
    def _update_audit_cache():
        """Update cache for audit statistics"""
        # Update daily counts cache
        today = timezone.now().date()
        today_count = AuditLog.objects.filter(
            created_at__date=today
        ).count()
        
        cache.set(f'audit_today_count_{today}', today_count, 86400)


class SystemHealthService:
    """
    Service for system health monitoring
    """
    
    @staticmethod
    def log_health_check(
        component: str,
        status: str,
        response_time_ms: float = None,
        memory_usage_mb: float = None,
        cpu_usage_percent: float = None,
        message: str = '',
        error_details: str = ''
    ) -> SystemHealthLog:
        """
        Log system health check
        """
        return SystemHealthLog.objects.create(
            component=component,
            status=status,
            response_time_ms=response_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            message=message,
            error_details=error_details
        )
    
    @staticmethod
    def get_current_health_status() -> Dict:
        """
        Get current health status of all components
        """
        components = SystemHealthLog.objects.values(
            'component'
        ).distinct()
        
        status_data = {}
        
        for component in components:
            comp_name = component['component']
            latest = SystemHealthLog.objects.filter(
                component=comp_name
            ).order_by('-created_at').first()
            
            if latest:
                status_data[comp_name] = {
                    'status': latest.status,
                    'last_checked': latest.created_at,
                    'response_time_ms': latest.response_time_ms,
                    'message': latest.message
                }
        
        # Calculate overall system health
        overall_status = 'HEALTHY'
        if any(data['status'] == 'CRITICAL' for data in status_data.values()):
            overall_status = 'CRITICAL'
        elif any(data['status'] == 'ERROR' for data in status_data.values()):
            overall_status = 'ERROR'
        elif any(data['status'] == 'WARNING' for data in status_data.values()):
            overall_status = 'WARNING'
        
        return {
            'overall_status': overall_status,
            'components': status_data,
            'timestamp': timezone.now()
        }
    
    @staticmethod
    def get_health_history(
        component: str,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get health history for a component
        """
        since = timezone.now() - timedelta(hours=hours)
        
        history = SystemHealthLog.objects.filter(
            component=component,
            created_at__gte=since
        ).order_by('created_at').values(
            'created_at', 'status', 'response_time_ms',
            'memory_usage_mb', 'cpu_usage_percent', 'message'
        )
        
        return list(history)