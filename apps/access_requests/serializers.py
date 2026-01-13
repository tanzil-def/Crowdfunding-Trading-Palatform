"""
Access Request Serializers - Clean DRF Implementation
Validation, transformation, and business logic encapsulation
"""

from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import AccessRequest, AccessRequestHistory
from apps.users.serializers import UserMinimalSerializer
from apps.projects.serializers import ProjectListSerializer


class AccessRequestSerializer(serializers.ModelSerializer):
    """
    Main serializer for AccessRequest model.
    Includes nested serializers for related objects.
    """
    
    investor = UserMinimalSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name',
        read_only=True
    )
    days_pending = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AccessRequest
        fields = [
            'id',
            'investor',
            'project',
            'status',
            'purpose',
            'requested_fields',
            'reviewed_by_name',
            'review_notes',
            'reviewed_at',
            'created_at',
            'updated_at',
            'days_pending',
            'has_access'
        ]
        read_only_fields = [
            'id', 'investor', 'status', 'reviewed_by_name',
            'review_notes', 'reviewed_at', 'created_at',
            'updated_at', 'days_pending', 'has_access'
        ]


class AccessRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new access requests.
    Includes business rule validation.
    """
    
    class Meta:
        model = AccessRequest
        fields = ['project', 'purpose', 'requested_fields']
        extra_kwargs = {
            'purpose': {'required': False, 'allow_blank': True},
            'requested_fields': {'required': False, 'default': list}
        }
    
    def validate(self, attrs):
        """Business validation for access request creation"""
        request = self.context.get('request')
        user = request.user
        project = attrs.get('project')
        
        if not user:
            raise serializers.ValidationError(_('Authentication required'))
        
        # SRS 5.1: Only verified investors can request access
        if not user.is_verified:
            raise serializers.ValidationError({
                'investor': _('Email verification required to request access')
            })
        
        # SRS 3.1: Only investors can request access
        if not user.is_investor:
            raise serializers.ValidationError({
                'investor': _('Only investors can request access to restricted data')
            })
        
        # SRS 5.4: Only approved projects can have access requests
        if project.status != 'APPROVED':
            raise serializers.ValidationError({
                'project': _('Can only request access to approved projects')
            })
        
        # Check for existing active request
        existing = AccessRequest.objects.filter(
            investor=user,
            project=project,
            status__in=[AccessRequest.Status.PENDING, AccessRequest.Status.APPROVED]
        ).exists()
        
        if existing:
            raise serializers.ValidationError({
                'project': _('You already have an active access request for this project')
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create access request with investor from request context"""
        validated_data['investor'] = self.context['request'].user
        return AccessRequest.objects.create(**validated_data)


class AccessRequestReviewSerializer(serializers.Serializer):
    """
    Serializer for admin review actions.
    Used for approve, reject, and revoke operations.
    """
    
    ACTION_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('revoke', _('Revoke'))
    ]
    
    action = serializers.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        help_text=_('Action to perform on the access request')
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=_('Optional notes explaining the decision')
    )
    
    def validate(self, attrs):
        """Validate review action based on current request status"""
        action = attrs['action']
        access_request = self.instance
        
        if not access_request:
            raise serializers.ValidationError(_('Access request not found'))
        
        # Validate action based on current status
        if action == 'approve' and access_request.status != AccessRequest.Status.PENDING:
            raise serializers.ValidationError({
                'action': _('Can only approve pending requests')
            })
        
        if action == 'reject' and access_request.status != AccessRequest.Status.PENDING:
            raise serializers.ValidationError({
                'action': _('Can only reject pending requests')
            })
        
        if action == 'revoke' and access_request.status != AccessRequest.Status.APPROVED:
            raise serializers.ValidationError({
                'action': _('Can only revoke approved requests')
            })
        
        return attrs


class AccessRequestHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for access request history entries.
    Read-only for audit trail.
    """
    
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name',
        read_only=True
    )
    changed_by_email = serializers.CharField(
        source='changed_by.email',
        read_only=True
    )
    
    class Meta:
        model = AccessRequestHistory
        fields = [
            'id',
            'previous_status',
            'new_status',
            'changed_by_name',
            'changed_by_email',
            'changed_at',
            'notes',
            'metadata'
        ]
        read_only_fields = fields


class AccessRequestStatsSerializer(serializers.Serializer):
    """
    Serializer for access request statistics.
    Used for admin dashboard.
    """
    
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_today = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    avg_processing_time_hours = serializers.FloatField()
    
    top_projects = serializers.ListField(
        child=serializers.DictField()
    )
    status_distribution = serializers.DictField()
    
    class Meta:
        fields = [
            'total_requests',
            'pending_requests',
            'approved_today',
            'approval_rate',
            'avg_processing_time_hours',
            'top_projects',
            'status_distribution'
        ]