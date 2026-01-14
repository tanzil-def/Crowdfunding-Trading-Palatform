import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with role-based access and Google OAuth support.
    
    SRS Requirements:
    - Email-based authentication
    - Role selection (Admin, Developer, Investor)
    - Email verification
    - Google OAuth integration
    """
    
    ROLE_ADMIN = 'ADMIN'
    ROLE_DEVELOPER = 'DEVELOPER'
    ROLE_INVESTOR = 'INVESTOR'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DEVELOPER, 'Developer'),
        (ROLE_INVESTOR, 'Investor'),
    ]
    
    AUTH_METHOD_EMAIL = 'EMAIL'
    AUTH_METHOD_GOOGLE = 'GOOGLE'
    
    AUTH_METHOD_CHOICES = [
        (AUTH_METHOD_EMAIL, 'Email/Password'),
        (AUTH_METHOD_GOOGLE, 'Google OAuth'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        db_index=True
    )
    first_name = models.CharField(
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True
    )
    auth_method = models.CharField(
        max_length=20,
        choices=AUTH_METHOD_CHOICES,
        default=AUTH_METHOD_EMAIL
    )
    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="Google OAuth user ID"
    )
    profile_picture = models.URLField(
        blank=True,
        null=True,
        help_text="Profile picture URL from Google or uploaded"
    )
    is_email_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Email verification status - required for investments"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="User account active status"
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Admin panel access"
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['is_email_verified']),
            models.Index(fields=['google_id']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Return full name or email if name not set."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """Return first name or email."""
        return self.first_name if self.first_name else self.email
    
    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_developer(self):
        """Check if user is developer."""
        return self.role == self.ROLE_DEVELOPER
    
    @property
    def is_investor(self):
        """Check if user is investor."""
        return self.role == self.ROLE_INVESTOR
    
    @property
    def can_invest(self):
        """
        Check if user can invest.
        SRS Requirement: Email verification required for investing.
        """
        return self.is_investor and self.is_email_verified
    
    def save(self, *args, **kwargs):
        """
        Auto-verify email for Google OAuth users.
        Admins bypass email verification.
        """
        if self.auth_method == self.AUTH_METHOD_GOOGLE and not self.is_email_verified:
            self.is_email_verified = True
        
        if self.role == self.ROLE_ADMIN:
            self.is_staff = True
            self.is_email_verified = True
        
        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """
    Email verification tokens sent to users.
    SRS Requirement: Email verification required.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and unused."""
        return not self.is_used and not self.is_expired


class PasswordResetToken(models.Model):
    """
    Password reset tokens sent to users.
    SRS Requirement: Password reset via email.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and unused."""
        return not self.is_used and not self.is_expired