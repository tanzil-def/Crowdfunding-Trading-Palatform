"""
Audit Serializers - Clean DRF Implementation
Read-only serializers for audit trail data
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import AuditLog, SystemHealthLog
from apps.users.serializers import UserMinimalSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Main serializer for AuditLog model.
    Includes nested serializers and calculated fields.
    """
    
    actor_details = UserMinimalSerializer(source='actor', read_only=True)
    action_type_display = serializers.CharField(
        source='get_action_type_display',
        read_only=True
    )
    action_category_display = serializers.CharField(
        source='get_action_category_display',
        read_only=True
    )
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action_category',
            'action_category_display',
            'action_type',
            'action_type_display',
            'actor',
            'actor_details',
            'actor_ip',
            'actor_user_agent',
            'target_model',
            'target_id',
            'description',
            'metadata',
            'created_at'
        ]
        read_only_fields = fields


class AuditLogFilterSerializer(serializers.Serializer):
    """
    Serializer for audit log filtering parameters.
    Used in query parameter validation.
    """
    
    action_type = serializers.CharField(required=False)
    action_category = serializers.CharField(required=False)
    target_model = serializers.CharField(required=False)
    target_id = serializers.UUIDField(required=False)
    actor_id = serializers.UUIDField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    
    def validate(self, attrs):
        """Validate filter parameters"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'start_date': _('Start date must be before end date')
            })
        
        return attrs


class AuditLogSummarySerializer(serializers.Serializer):
    """
    Serializer for audit log summary statistics.
    """
    
    total_logs = serializers.IntegerField()
    logs_today = serializers.IntegerField()
    logs_this_week = serializers.IntegerField()
    logs_this_month = serializers.IntegerField()
    
    by_category = serializers.DictField()
    by_action_type = serializers.DictField()
    
    top_actors = serializers.ListField(
        child=serializers.DictField()
    )
    recent_actions = serializers.ListField(
        child=serializers.DictField()
    )
    
    class Meta:
        fields = [
            'total_logs',
            'logs_today',
            'logs_this_week',
            'logs_this_month',
            'by_category',
            'by_action_type',
            'top_actors',
            'recent_actions'
        ]


class SystemHealthLogSerializer(serializers.ModelSerializer):
    """
    Serializer for system health logs.
    """
    
    class Meta:
        model = SystemHealthLog
        fields = [
            'id',
            'component',
            'status',
            'response_time_ms',
            'memory_usage_mb',
            'cpu_usage_percent',
            'message',
            'error_details',
            'metadata',
            'created_at'
        ]
        read_only_fields = fields


class AuditExportSerializer(serializers.Serializer):
    """
    Serializer for audit log export configuration.
    """
    
    format = serializers.ChoiceField(
        choices=['csv', 'json', 'pdf'],
        default='csv'
    )
    include_columns = serializers.ListField(
        child=serializers.CharField(),
        default=['action_type', 'actor', 'target_model', 'target_id', 'created_at']
    )
    filters = AuditLogFilterSerializer(required=False)
    
    class Meta:
        fields = ['format', 'include_columns', 'filters']