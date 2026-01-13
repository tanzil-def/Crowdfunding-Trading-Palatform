import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model matching SRS requirements"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DEVELOPER = 'DEVELOPER', 'Developer'
        INVESTOR = 'INVESTOR', 'Investor'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # SRS Requirement: Role-based access
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.INVESTOR
    )
    
    # SRS Requirement: Email verification required for investing
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Profile fields
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # For password reset
    reset_token = models.UUIDField(null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email', 'is_verified']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_investor(self):
        return self.role == self.Role.INVESTOR
    
    @property
    def is_developer(self):
        return self.role == self.Role.DEVELOPER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def send_verification_email(self, request=None):
        """Send email verification link"""
        from django.conf import settings
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{self.verification_token}/"
        
        subject = "Verify Your Email - Crowdfunding Trading Platform"
        html_message = render_to_string('emails/verification.html', {
            'user': self,
            'verification_url': verification_url,
        })
        
        send_mail(
            subject=subject,
            message=f"Please verify your email: {verification_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message,
        )
        
        self.verification_sent_at = timezone.now()
        self.save(update_fields=['verification_sent_at'])


class Wallet(models.Model):
    """User wallet for refunds/withdrawals (SRS: Payment handling)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
    
    def __str__(self):
        return f"Wallet({self.user.email}): ${self.balance}"


class WalletTransaction(models.Model):
    """Wallet transaction history for audit trail"""
    
    class TransactionType(models.TextChoices):
        REFUND = 'REFUND', 'Refund'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        INVESTMENT = 'INVESTMENT', 'Investment'
        REVERSAL = 'REVERSAL', 'Reversal'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    
    # Reference to related entities (for audit trail)
    reference_id = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=50, blank=True)  # e.g., 'investment', 'project'
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_id', 'reference_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.type}: ${self.amount} ({self.created_at.date()})"