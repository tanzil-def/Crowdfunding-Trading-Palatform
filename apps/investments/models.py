import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User
from apps.projects.models import Project


class InvestmentRequest(models.Model):
    """
    Main entity tracking the investment lifecycle from initiation to share allocation.
    
    Status transitions:
    PENDING_PAYMENT -> (PAYMENT_FAILED, PAYMENT_CONFIRMED, CANCELLED)
    PAYMENT_CONFIRMED -> (ADMIN_APPROVED, ADMIN_REJECTED)
    ADMIN_APPROVED -> SHARES_ALLOCATED
    """
    STATUS_PENDING_PAYMENT = 'PENDING_PAYMENT'
    STATUS_PAYMENT_FAILED = 'PAYMENT_FAILED'
    STATUS_PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED'
    STATUS_ADMIN_APPROVED = 'ADMIN_APPROVED'
    STATUS_ADMIN_REJECTED = 'ADMIN_REJECTED'
    STATUS_SHARES_ALLOCATED = 'SHARES_ALLOCATED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Pending Payment'),
        (STATUS_PAYMENT_FAILED, 'Payment Failed'),
        (STATUS_PAYMENT_CONFIRMED, 'Payment Confirmed'),
        (STATUS_ADMIN_APPROVED, 'Admin Approved'),
        (STATUS_ADMIN_REJECTED, 'Admin Rejected'),
        (STATUS_SHARES_ALLOCATED, 'Shares Allocated'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='investment_requests')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='investment_requests')
    
    requested_shares = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_share = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT, db_index=True)
    
    payment_reference = models.CharField(max_length=255, unique=True, db_index=True)
    payment_url = models.URLField(max_length=1000, null=True, blank=True)
    
    admin_remarks = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_investment_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['project', 'status']),
        ]

    def __str__(self):
        return f"REQ {self.payment_reference} - {self.investor.email} - {self.status}"


class PaymentTransaction(models.Model):
    """
    Detailed gateway-level transaction logs. 
    Distinct from InvestmentRequest to track multiple attempts if needed.
    """
    STATUS_INITIATED = 'INITIATED'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_REFUNDED = 'REFUNDED'

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment_request = models.ForeignKey(InvestmentRequest, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    
    gateway_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED, db_index=True)
    raw_gateway_response = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_payment_transaction'


class PortfolioHolding(models.Model):
    """
    aggregated view of an investor's holdings in a project.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='portfolio_holdings')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='portfolio_holdings')
    
    shares_owned = models.PositiveIntegerField(default=0)
    avg_buy_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_portfolio_holding'
        unique_together = ('investor', 'project')

    def __str__(self):
        return f"{self.investor.email} holding in {self.project.title}"


class ShareLedger(models.Model):
    """
    Immutable ledger of all share movements.
    This is the source of truth for all accounting.
    """
    REASON_PURCHASE = 'PURCHASE'
    REASON_REFUND = 'REFUND'
    REASON_ADJUSTMENT = 'ADJUSTMENT'

    REASON_CHOICES = [
        (REASON_PURCHASE, 'Purchase'),
        (REASON_REFUND, 'Refund'),
        (REASON_ADJUSTMENT, 'Adjustment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment_request = models.ForeignKey(InvestmentRequest, on_delete=models.PROTECT, related_name='ledger_entries', null=True, blank=True)
    
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ledger_entries')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='ledger_entries')
    
    shares_delta = models.IntegerField(help_text="Positive for purchase, negative for withdrawal/refund")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'investments_share_ledger'


class SharePurchase(models.Model):
    """
    Kept for backward compatibility and receipt generation.
    In the new flow, this is created upon ADMIN_APPROVED -> SHARES_ALLOCATED.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='share_purchases')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='share_purchases')
    
    investment_request = models.OneToOneField(InvestmentRequest, on_delete=models.PROTECT, related_name='share_purchase', null=True, blank=True)
    # payment_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.PROTECT, related_name='share_purchase', null=True) # Replaced by investment_request
    
    shares_purchased = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_share = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'investments_share_purchase'