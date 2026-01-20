from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from decimal import Decimal
from .models import SharePurchase, PaymentTransaction
from utils.exceptions import ResourceConflictError


class InitiateInvestmentSerializer(serializers.Serializer):
    """
    Request serializer for initiating investment process.
    
    SRS Requirements:
    - Email verification required (enforced in service layer)
    - Only approved projects (enforced in service layer)
    - Share availability check (enforced in service layer)
    - Idempotency support via idempotency_key
    """
    project_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the project to invest in"
    )
    shares_requested = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            'min_value': 'You must purchase at least 1 share.',
            'required': 'Number of shares is required.'
        },
        help_text="Number of shares to purchase"
    )
    idempotency_key = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            'required': 'Idempotency key is required to prevent duplicate transactions.'
        },
        help_text="Unique key to prevent duplicate transactions"
    )

    def validate_idempotency_key(self, value):
        """
        Ensure idempotency key is unique.
        SRS: Raises 409 Conflict if already exists.
        """
        if PaymentTransaction.objects.filter(reference_id=value).exists():
            raise ResourceConflictError(
                f"Duplicate transaction detected for key: {value}"
            )
        return value


class InvestmentInitiateResponseSerializer(serializers.Serializer):
    """
    Response serializer for investment initiation.
    
    Returns payment details including URL for gateway redirect.
    """
    project_id = serializers.UUIDField(
        read_only=True,
        help_text="UUID of the project"
    )
    shares_requested = serializers.IntegerField(
        read_only=True,
        help_text="Number of shares requested"
    )
    idempotency_key = serializers.CharField(
        read_only=True,
        help_text="Transaction reference ID"
    )
    reference_id = serializers.UUIDField(
        read_only=True,
        help_text="Payment transaction UUID"
    )
    payment_url = serializers.URLField(
        read_only=True,
        help_text="URL to redirect user for payment"
    )


class PaymentCallbackSerializer(serializers.Serializer):
    """
    Serializer for payment gateway callback.
    
    SRS Requirements:
    - Idempotent processing (enforced in service layer)
    - Prevents duplicate callbacks (enforced in service layer)
    - Atomic share allocation (enforced in service layer)
    - Audit logging (enforced in service layer)
    
    Validates callback data from external payment provider.
    """
    payment_reference_id = serializers.CharField(
        required=True,
        help_text="Reference ID of the payment transaction"
    )
    success = serializers.BooleanField(
        required=True,
        help_text="Whether payment was successful"
    )
    gateway_payload = serializers.JSONField(
        required=True,
        help_text="Raw payload from payment gateway"
    )

    def validate_payment_reference_id(self, value):
        """
        Ensure payment reference exists.
        """
        if not PaymentTransaction.objects.filter(reference_id=value).exists():
            raise serializers.ValidationError(
                "Invalid payment reference. Transaction not found."
            )
        return value

    def validate_gateway_payload(self, value):
        """
        Ensure required keys exist in gateway payload.
        Validates structure and presence of critical payment fields.
        """
        required_fields = ['shares_requested', 'project_id', 'investor_id', 'txn_id', 'amount']
        missing = [f for f in required_fields if f not in value]
        if missing:
            raise serializers.ValidationError(
                f"Gateway payload missing required fields: {', '.join(missing)}"
            )
        
        # Type validation for critical fields
        if not isinstance(value.get('shares_requested'), int):
            raise serializers.ValidationError(
                "Field 'shares_requested' must be an integer."
            )
        
        if not isinstance(value.get('amount'), (str, int, float)):
            raise serializers.ValidationError(
                "Field 'amount' must be a string or number."
            )
        
        return value

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'shares_requested': {'type': 'integer', 'example': 2},
            'project_id': {'type': 'string', 'format': 'uuid', 'example': '71b7d9e6-f29a-46e0-9899-f0dd317403a7'},
            'investor_id': {'type': 'string', 'format': 'uuid', 'example': '8d4594d3-7a6c-430d-bfbe-d521316deba2'},
            'txn_id': {'type': 'string', 'example': 'TXN001'},
            'amount': {'type': 'string', 'example': '93.06'}
        },
        'required': ['shares_requested', 'project_id', 'investor_id', 'txn_id', 'amount']
    })
    def get_gateway_payload(self):
        return None


class SharePurchaseListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing investor's share purchases.
    
    SRS Requirements:
    - Show investment history
    - Include project details
    - Ordered by most recent (enforced in view queryset)
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
    Used for receipts and transaction details.
    
    SRS Requirements:
    - Retrieve detailed information about specific investment
    - Include project status and share information
    - Include payment transaction details
    """
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_status = serializers.CharField(source='project.status', read_only=True)
    project_total_shares = serializers.IntegerField(source='project.total_shares', read_only=True)
    project_shares_sold = serializers.SerializerMethodField()
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

    @extend_schema_field(serializers.IntegerField())
    def get_project_shares_sold(self, obj):
        """
        Dynamically calculate shares sold from project.
        SRS: Ensure real-time accuracy of shares sold.
        """
        return obj.project.shares_sold

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'reference_id': {'type': 'string'},
            'status': {'type': 'string'},
            'processed_at': {'type': 'string', 'format': 'date-time', 'nullable': True}
        }
    })
    def get_payment_details(self, obj):
        """
        Include payment transaction details for receipt purposes.
        SRS: Provide complete transaction information for audit trail.
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
    
    SRS Requirements:
    - Admin can review all transactions
    - Includes success and failures
    - Audit trail support
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

    @extend_schema_field(serializers.BooleanField())
    def get_has_share_purchase(self, obj):
        """
        Check if transaction resulted in share purchase.
        SRS: Distinguish between successful and failed transactions.
        """
        return hasattr(obj, 'share_purchase')


class PortfolioSummarySerializer(serializers.Serializer):
    """
    Serializer for investor portfolio summary.
    
    SRS Requirements:
    - Total invested amount
    - Number of projects invested
    - Total shares owned
    - Investment count
    """
    total_invested = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount invested across all projects"
    )
    projects_invested = serializers.IntegerField(
        help_text="Number of unique projects invested in"
    )
    total_shares_owned = serializers.IntegerField(
        help_text="Total number of shares owned across all projects"
    )
    investment_count = serializers.IntegerField(
        help_text="Total number of investment transactions"
    )