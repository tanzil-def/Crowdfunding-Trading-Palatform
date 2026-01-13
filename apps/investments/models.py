import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BaseAuditModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        verbose_name=_('Updated At')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_%(class)s_set',
        verbose_name=_('Created By')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Investment(BaseAuditModel):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        APPROVED = 'APPROVED', _('Approved')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        REJECTED = 'REJECTED', _('Rejected')
        CANCELLED = 'CANCELLED', _('Cancelled')
        EXPIRED = 'EXPIRED', _('Expired')
        REFUNDED = 'REFUNDED', _('Refunded')
        WITHDRAWN = 'WITHDRAWN', _('Withdrawn')

    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments',
        verbose_name=_('Investor'),
        limit_choices_to={'role': 'INVESTOR', 'is_verified': True}
    )

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='investments',
        verbose_name=_('Project'),
        limit_choices_to={'status': 'APPROVED'}
    )

    shares = models.PositiveIntegerField(
        verbose_name=_('Shares Purchased'),
        validators=[MinValueValidator(1)],
        help_text=_('Number of shares to purchase')
    )

    price_per_share = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Price per Share'),
        help_text=_('Calculated: Total Project Value ÷ Total Shares')
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name=_('Total Investment'),
        editable=False,
        help_text=_('Calculated: Shares Purchased × Per Share Price')
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
        verbose_name=_('Status')
    )

    approval_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approval Expiry')
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Reviewed At')
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_investments',
        verbose_name=_('Reviewed By')
    )

    investor_notes = models.TextField(
        blank=True,
        verbose_name=_('Investor Notes')
    )

    admin_notes = models.TextField(
        blank=True,
        verbose_name=_('Admin Notes')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed At')
    )

    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Refunded At')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )

    class Meta:
        db_table = 'investments'
        verbose_name = _('Investment')
        verbose_name_plural = _('Investments')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['investor', 'project'],
                condition=models.Q(status__in=['REQUESTED', 'APPROVED', 'PROCESSING']),
                name='unique_active_investment_per_project'
            )
        ]
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at', 'investor']),
        ]

    def __str__(self):
        return f'{self.investor.email} → {self.project.title} ({self.shares} shares)'

    def clean(self):
        super().clean()

        if self.shares and self.price_per_share:
            self.total_amount = Decimal(self.shares) * Decimal(str(self.price_per_share))

        if self.project and self.shares:
            if hasattr(self.project, 'remaining_shares'):
                available_shares = self.project.remaining_shares

                if self.status in ['REQUESTED', 'APPROVED', 'PROCESSING']:
                    if self.shares > available_shares:
                        raise ValidationError({
                            'shares': _('Only %(available)s shares available') % {
                                'available': available_shares
                            }
                        })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in [
            self.Status.REQUESTED,
            self.Status.APPROVED,
            self.Status.PROCESSING
        ]

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def is_expired(self):
        if self.status == self.Status.APPROVED and self.approval_expires_at:
            return timezone.now() > self.approval_expires_at
        return False


class PaymentTransaction(BaseAuditModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class PaymentMethod(models.TextChoices):
        CARD = 'CARD', _('Credit/Debit Card')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        DIGITAL_WALLET = 'DIGITAL_WALLET', _('Digital Wallet')
        SANDBOX = 'SANDBOX', _('Sandbox (Testing)')

    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_('Transaction ID')
    )

    reference_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_('Idempotency Key'),
        help_text=_('Prevents duplicate payment processing')
    )

    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Investment')
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name=_('Payment Amount')
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_('Status')
    )

    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        default=PaymentMethod.SANDBOX,
        verbose_name=_('Payment Method')
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Gateway Response')
    )

    gateway_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Gateway Transaction ID')
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Processed At')
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference_id']),
            models.Index(fields=['investment', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'{self.transaction_id} - {self.amount} - {self.status}'

    @property
    def is_successful(self):
        return self.status == self.Status.SUCCESS

    def mark_successful(self, gateway_data=None):
        self.status = self.Status.SUCCESS
        self.processed_at = timezone.now()

        if gateway_data:
            self.gateway_response = gateway_data
            self.gateway_transaction_id = gateway_data.get('transaction_id', '')

        self.save()

        self.investment.status = Investment.Status.PROCESSING
        self.investment.save(update_fields=['status', 'updated_at'])

    def mark_failed(self, error_message=''):
        self.status = self.Status.FAILED
        self.processed_at = timezone.now()

        if error_message:
            self.gateway_response = self.gateway_response or {}
            self.gateway_response['error'] = error_message

        self.save()


class InvestmentAuditLog(models.Model):
    class ActionType(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        PAYMENT_INITIATED = 'PAYMENT_INITIATED', _('Payment Initiated')
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', _('Payment Success')
        PAYMENT_FAILED = 'PAYMENT_FAILED', _('Payment Failed')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REFUNDED = 'REFUNDED', _('Refunded')
        WITHDRAWN = 'WITHDRAWN', _('Withdrawn')
        EXPIRED = 'EXPIRED', _('Expired')
        UPDATED = 'UPDATED', _('Updated')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('Investment')
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='investment_audit_actions',
        verbose_name=_('Actor')
    )

    actor_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Actor IP Address')
    )

    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        verbose_name=_('Action Type')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    previous_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Previous Status')
    )

    new_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('New Status')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Created At')
    )

    class Meta:
        db_table = 'investment_audit_logs'
        verbose_name = _('Investment Audit Log')
        verbose_name_plural = _('Investment Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investment', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
        ]

    def __str__(self):
        return f'{self.action_type} - Investment #{self.investment.id[:8]}'