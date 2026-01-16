from rest_framework import serializers
from decimal import Decimal
from .models import SharePurchase, PaymentTransaction
from utils.exceptions import ResourceConflictError


class InitiateInvestmentSerializer(serializers.Serializer):
    """
    Serializer for initiating investment process.
    Validates input before creating payment transaction.
    """
    project_id = serializers.UUIDField(required=True)
    shares_requested = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            'min_value': 'You must purchase at least 1 share.',
            'required': 'Number of shares is required.'
        }
    )
    idempotency_key = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            'required': 'Idempotency key is required to prevent duplicate transactions.'
        }
    )

    def validate_idempotency_key(self, value):
        """
        Ensure idempotency key is unique.
        Raises 409 Conflict if already exists.
        """
        if PaymentTransaction.objects.filter(reference_id=value).exists():
            raise ResourceConflictError(
                f"Duplicate transaction detected for key: {value}"
            )
        return value


class PaymentCallbackSerializer(serializers.Serializer):
    """
    Serializer for payment gateway callback.
    Validates callback data from external payment provider.
    """
    payment_reference_id = serializers.CharField(required=True)
    success = serializers.BooleanField(required=True)
    gateway_payload = serializers.JSONField(required=True)

    def validate_payment_reference_id(self, value):
        """
        Ensure payment reference exists.
        """
        if not PaymentTransaction.objects.filter(reference_id=value).exists():
            raise serializers.ValidationError(
                "Invalid payment reference. Transaction not found."
            )
        return value


class SharePurchaseListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing investor's share purchases.
    Includes project details for easy reference.
    """
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_category = serializers.CharField(source='project.category', read_only=True)
    payment_status = serializers.CharField(source='payment.status', read_only=True)
    payment_reference = serializers.CharField(source='payment.reference_id', read_only=True)

    class Meta:
        model = SharePurchase
        fields = [
            'id',
            'project_id',
            'project_title',
            'project_category',
            'shares_purchased',
            'price_per_share',
            'total_amount',
            'payment_status',
            'payment_reference',
            'created_at'
        ]
        read_only_fields = fields


class SharePurchaseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual share purchase.
    Used in dashboard and transaction history.
    """
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_status = serializers.CharField(source='project.status', read_only=True)
    project_total_shares = serializers.IntegerField(source='project.total_shares', read_only=True)
    project_shares_sold = serializers.IntegerField(source='project.shares_sold', read_only=True)
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = SharePurchase
        fields = [
            'id',
            'project_id',
            'project_title',
            'project_status',
            'project_total_shares',
            'project_shares_sold',
            'shares_purchased',
            'price_per_share',
            'total_amount',
            'payment_details',
            'created_at'
        ]
        read_only_fields = fields

    def get_payment_details(self, obj):
        """
        Include payment transaction details for receipt purposes.
        """
        return {
            'reference_id': obj.payment.reference_id,
            'status': obj.payment.status,
            'processed_at': obj.payment.processed_at
        }


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for payment transaction records.
    Used in admin panel and audit logs.
    """
    investor_email = serializers.EmailField(source='investor.email', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    has_share_purchase = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'reference_id',
            'investor_email',
            'project_title',
            'amount',
            'status',
            'has_share_purchase',
            'failure_reason',
            'created_at',
            'processed_at'
        ]
        read_only_fields = fields

    def get_has_share_purchase(self, obj):
        """
        Check if this payment resulted in share purchase.
        """
        return hasattr(obj, 'share_purchase')