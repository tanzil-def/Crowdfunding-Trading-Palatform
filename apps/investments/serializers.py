from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal, ROUND_HALF_UP

from .models import Investment, PaymentTransaction
from apps.projects.models import Project
from apps.users.models import User


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for investment data display[citation:9]"""
    
    investor_name = serializers.CharField(source='investor.get_full_name', read_only=True)
    investor_email = serializers.CharField(source='investor.email', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_thumbnail = serializers.SerializerMethodField()
    remaining_shares = serializers.IntegerField(source='project.remaining_shares', read_only=True)
    can_cancel = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor', 'investor_name', 'investor_email',
            'project', 'project_title', 'project_thumbnail',
            'shares', 'price_per_share', 'total_amount', 'status',
            'approval_expires_at', 'investor_notes', 'admin_notes',
            'created_at', 'reviewed_at', 'completed_at',
            'remaining_shares', 'can_cancel', 'can_pay'
        ]
        read_only_fields = [
            'id', 'investor', 'price_per_share', 'total_amount', 'status',
            'created_at', 'reviewed_at', 'completed_at'
        ]
    
    def get_project_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.project.thumbnail and request:
            return request.build_absolute_uri(obj.project.thumbnail.url)
        return None
    
    def get_can_cancel(self, obj):
        """Check if investment can be cancelled by investor"""
        return obj.status in [Investment.Status.REQUESTED, Investment.Status.APPROVED]
    
    def get_can_pay(self, obj):
        """Check if payment can be initiated"""
        return (
            obj.status == Investment.Status.APPROVED and
            obj.approval_expires_at > timezone.now()
        )


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating investment requests[citation:1]"""
    
    class Meta:
        model = Investment
        fields = ['project', 'shares', 'investor_notes']
        extra_kwargs = {
            'shares': {'min_value': 1},
            'investor_notes': {'required': False, 'allow_blank': True}
        }
    
    def validate(self, attrs):
        """Comprehensive validation for investment creation"""
        user = self.context['request'].user
        project = attrs['project']
        shares = attrs['shares']
        
        # SRS: Unverified investors cannot invest
        if not user.is_verified:
            raise serializers.ValidationError({
                'investor': 'Email verification required before investing'
            })
        
        # Check user ban status
        if user.is_banned:
            raise serializers.ValidationError({
                'investor': 'Account is restricted from investing'
            })
        
        # Validate project status
        if project.status != Project.Status.APPROVED:
            raise serializers.ValidationError({
                'project': 'Only approved projects are available for investment'
            })
        
        # Validate share availability
        if shares > project.remaining_shares:
            raise serializers.ValidationError({
                'shares': f'Only {project.remaining_shares} shares available'
            })
        
        # Check for existing active investment
        existing = Investment.objects.filter(
            investor=user,
            project=project,
            status__in=[
                Investment.Status.REQUESTED,
                Investment.Status.APPROVED,
                Investment.Status.PROCESSING
            ]
        ).exists()
        
        if existing:
            raise serializers.ValidationError({
                'project': 'You already have an active investment request for this project'
            })
        
        # Calculate price per share
        attrs['price_per_share'] = project.per_share_price
        attrs['total_amount'] = Decimal(shares) * project.per_share_price
        
        return attrs
    
    def create(self, validated_data):
        """Create investment with investor from request context"""
        validated_data['investor'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class InvestmentReviewSerializer(serializers.Serializer):
    """Serializer for admin review of investments[citation:7]"""
    
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        required=True
    )
    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )
    expires_in_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        default=7
    )
    
    def validate(self, attrs):
        # Additional validation can be added here
        return attrs


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions[citation:9]"""
    
    investment_details = InvestmentSerializer(
        source='investment',
        read_only=True
    )
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'transaction_id', 'reference_id',
            'investment', 'investment_details',
            'amount', 'status', 'payment_method',
            'gateway_transaction_id', 'processed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'reference_id',
            'amount', 'status', 'gateway_transaction_id',
            'processed_at', 'created_at', 'updated_at'
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating payment[citation:1]"""
    
    payment_method = serializers.ChoiceField(
        choices=PaymentTransaction.PaymentMethod.choices,
        default=PaymentTransaction.PaymentMethod.SANDBOX
    )
    reference_id = serializers.CharField(
        max_length=255,
        required=True,
        help_text='Idempotency key to prevent duplicate payments'
    )
    
    def validate_reference_id(self, value):
        """Ensure reference_id is unique"""
        if PaymentTransaction.objects.filter(reference_id=value).exists():
            raise serializers.ValidationError(
                'Duplicate payment request detected'
            )
        return value