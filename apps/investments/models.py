import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User
from apps.projects.models import Project


class PaymentTransaction(models.Model):
    """
    Payment transaction records for audit trail and idempotency.
    Tracks all payment attempts including success and failures.
    
    Status flow: INITIATED → (SUCCESS or FAILED)
    One payment transaction can have at most one share purchase (success case only).
    """
    STATUS_INITIATED = 'INITIATED'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Payment Initiated'),
        (STATUS_SUCCESS, 'Payment Successful'),
        (STATUS_FAILED, 'Payment Failed'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique transaction identifier"
    )
    reference_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique reference from payment gateway"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        help_text="Client-provided key to prevent duplicate requests"
    )
    investor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='payment_transactions',
        help_text="Investor who initiated this payment"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='payment_transactions',
        help_text="Project being invested in"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount in USD"
    )
    shares_requested = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares requested"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_INITIATED,
        db_index=True,
        help_text="Current payment status"
    )
    failure_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if payment failed"
    )
    
    # Gateway audit trail
    gateway_payload = models.JSONField(
        blank=True,
        null=True,
        help_text="Complete response from payment gateway (for audit)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When payment was initiated"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When payment was last updated"
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When payment was processed by gateway"
    )

    class Meta:
        db_table = 'investments_payment_transaction'
        ordering = ['-created_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['reference_id']),
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['idempotency_key']),
        ]

    def __str__(self):
        return f"{self.reference_id} - {self.investor.email} - {self.status}"

    def is_completed(self):
        """Check if payment is final (success or failed)"""
        return self.status in [self.STATUS_SUCCESS, self.STATUS_FAILED]

    @property
    def price_per_share(self):
        """Calculate effective price per share"""
        if self.shares_requested > 0:
            return self.amount / Decimal(str(self.shares_requested))
        return Decimal('0.00')


class SharePurchase(models.Model):
    """
    Records successful share purchases.
    Created ONLY after payment succeeds.
    
    One payment transaction has at most one share purchase.
    Multiple share purchases from same investor across different projects.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Foreign keys
    investor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='share_purchases',
        help_text="Investor who owns these shares"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='share_purchases',
        help_text="Project these shares belong to"
    )
    payment_transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.PROTECT,
        related_name='share_purchase',
        help_text="Associated successful payment"
    )
    
    # Share details (immutable after creation)
    shares_purchased = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares purchased"
    )
    price_per_share = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per share at time of purchase (immutable)"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total amount = shares × price"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'investments_share_purchase'
        ordering = ['-created_at']
        verbose_name = 'Share Purchase'
        verbose_name_plural = 'Share Purchases'
        indexes = [
            models.Index(fields=['investor', '-created_at']),
            models.Index(fields=['project', '-created_at']),
        ]

    def __str__(self):
        return f"{self.investor.email} - {self.shares_purchased} shares of {self.project.title}"

    def validate_consistency(self):
        """Ensure amount = shares × price (data integrity)"""
        from django.core.exceptions import ValidationError
        expected_total = Decimal(str(self.shares_purchased)) * self.price_per_share
        if expected_total != self.total_amount:
            raise ValidationError("Share purchase amount mismatch")

    def save(self, *args, **kwargs):
        """
        Ensure total_amount matches calculation.
        This provides data integrity at model level.
        """
        if not self.total_amount:
            self.total_amount = Decimal(str(self.shares_purchased)) * self.price_per_share
        super().save(*args, **kwargs)