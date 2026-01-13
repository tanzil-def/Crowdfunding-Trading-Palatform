"""
Audit Models - SRS 5.12 Compliant
Immutable audit trail for all critical system actions
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField


class AuditLogManager(models.Manager):
    """Custom manager for AuditLog queries"""
    
    def for_target(self, target_model, target_id):
        """Get logs for a specific target"""
        return self.filter(
            target_model=target_model,
            target_id=target_id
        ).select_related('actor')
    
    def for_actor(self, actor_id):
        """Get logs created by a specific actor"""
        return self.filter(actor_id=actor_id).order_by('-created_at')
    
    def for_action_type(self, action_type):
        """Get logs of a specific action type"""
        return self.filter(action_type=action_type).order_by('-created_at')
    
    def create_log(self, action_type, actor, target_model, target_id, **kwargs):
        """Business method to create audit log"""
        return self.create(
            action_type=action_type,
            actor=actor,
            target_model=target_model,
            target_id=target_id,
            **kwargs
        )


class AuditLog(models.Model):
    """
    Immutable audit trail for all system actions.
    SRS Requirements: 5.3, 5.8, 5.12
    """
    
    class ActionCategory(models.TextChoices):
        AUTHENTICATION = 'AUTHENTICATION', _('Authentication')
        PROJECT = 'PROJECT', _('Project')
        ACCESS_CONTROL = 'ACCESS_CONTROL', _('Access Control')
        INVESTMENT = 'INVESTMENT', _('Investment')
        PAYMENT = 'PAYMENT', _('Payment')
        USER = 'USER', _('User')
        SYSTEM = 'SYSTEM', _('System')
    
    class ActionType(models.TextChoices):
        # Access Control (SRS 5.7)
        ACCESS_REQUESTED = 'ACCESS_REQUESTED', _('Access Requested')
        ACCESS_APPROVED = 'ACCESS_APPROVED', _('Access Approved')
        ACCESS_REJECTED = 'ACCESS_REJECTED', _('Access Rejected')
        ACCESS_REVOKED = 'ACCESS_REVOKED', _('Access Revoked')
        
        # Project (SRS 5.2, 5.3)
        PROJECT_CREATED = 'PROJECT_CREATED', _('Project Created')
        PROJECT_SUBMITTED = 'PROJECT_SUBMITTED', _('Project Submitted')
        PROJECT_APPROVED = 'PROJECT_APPROVED', _('Project Approved')
        PROJECT_REJECTED = 'PROJECT_REJECTED', _('Project Rejected')
        PROJECT_UPDATED = 'PROJECT_UPDATED', _('Project Updated')
        
        # Payment (SRS 5.8)
        PAYMENT_INITIATED = 'PAYMENT_INITIATED', _('Payment Initiated')
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', _('Payment Success')
        PAYMENT_FAILED = 'PAYMENT_FAILED', _('Payment Failed')
        PAYMENT_REFUNDED = 'PAYMENT_REFUNDED', _('Payment Refunded')
        
        # Investment (SRS 5.8)
        SHARES_PURCHASED = 'SHARES_PURCHASED', _('Shares Purchased')
        SHARES_ALLOCATED = 'SHARES_ALLOCATED', _('Shares Allocated')
        SHARES_CANCELLED = 'SHARES_CANCELLED', _('Shares Cancelled')
        
        # User (SRS 5.1)
        USER_REGISTERED = 'USER_REGISTERED', _('User Registered')
        USER_VERIFIED = 'USER_VERIFIED', _('User Verified')
        USER_UPDATED = 'USER_UPDATED', _('User Updated')
        USER_DELETED = 'USER_DELETED', _('User Deleted')
        
        # System
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', _('Password Change')
        PASSWORD_RESET = 'PASSWORD_RESET', _('Password Reset')
    
    # Core Fields
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    action_category = models.CharField(
        max_length=50,
        choices=ActionCategory.choices,
        db_index=True,
        verbose_name=_('Action Category')
    )
    action_type = models.CharField(
        max_length=100,
        choices=ActionType.choices,
        db_index=True,
        verbose_name=_('Action Type')
    )
    
    # Actor Information
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions',
        verbose_name=_('Actor')
    )
    actor_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Actor IP Address')
    )
    actor_user_agent = models.TextField(
        blank=True,
        verbose_name=_('Actor User Agent')
    )
    
    # Target Information
    target_model = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_('Target Model')
    )
    target_id = models.UUIDField(
        db_index=True,
        verbose_name=_('Target ID')
    )
    
    # Context
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    metadata = JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Created At')
    )
    
    # Manager
    objects = AuditLogManager()
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_category', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['target_model', 'target_id']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.action_type} - {self.target_model} - {self.created_at}'
    
    def save(self, *args, **kwargs):
        """Ensure audit logs are immutable"""
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValidationError(_('Audit logs are immutable and cannot be modified'))
        super().save(*args, **kwargs)
    
    @classmethod
    def log_access_request(cls, action_type, actor, access_request, metadata=None):
        """Helper to log access request actions"""
        return cls.objects.create(
            action_category=cls.ActionCategory.ACCESS_CONTROL,
            action_type=action_type,
            actor=actor,
            target_model='AccessRequest',
            target_id=access_request.id,
            description=f"Access request for project '{access_request.project.title}' by {access_request.investor.email}",
            metadata=metadata or {},
            actor_ip=getattr(actor, 'last_login_ip', None)
        )
    
    @classmethod
    def log_payment(cls, action_type, actor, payment, metadata=None):
        """Helper to log payment actions"""
        return cls.objects.create(
            action_category=cls.ActionCategory.PAYMENT,
            action_type=action_type,
            actor=actor,
            target_model='PaymentTransaction',
            target_id=payment.id,
            description=f"Payment {action_type.lower()} - Amount: {metadata.get('amount', 'N/A')}",
            metadata=metadata or {}
        )
    
    @classmethod
    def log_project_action(cls, action_type, actor, project, metadata=None):
        """Helper to log project actions"""
        return cls.objects.create(
            action_category=cls.ActionCategory.PROJECT,
            action_type=action_type,
            actor=actor,
            target_model='Project',
            target_id=project.id,
            description=f"Project '{project.title}' - {action_type}",
            metadata=metadata or {}
        )


class SystemHealthLog(models.Model):
    """
    System health monitoring logs.
    Used for troubleshooting and performance monitoring.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Health metrics
    component = models.CharField(max_length=100, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('HEALTHY', 'Healthy'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical')
        ],
        db_index=True
    )
    
    # Metrics
    response_time_ms = models.FloatField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    cpu_usage_percent = models.FloatField(null=True, blank=True)
    
    # Context
    message = models.TextField(blank=True)
    error_details = models.TextField(blank=True)
    metadata = JSONField(default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'system_health_logs'
        ordering = ['-created_at']
        verbose_name = _('System Health Log')
        verbose_name_plural = _('System Health Logs')
    
    def __str__(self):
        return f'{self.component} - {self.status} - {self.created_at}'