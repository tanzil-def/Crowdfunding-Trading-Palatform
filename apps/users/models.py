import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for crowdfunding platform.
    
    SRS Requirements Implemented:
    - Role-based access control (Admin, Developer, Investor)
    - Email verification enforcement
    - OAuth support (Google)
    - Secure authentication
    """
    
    ROLE_ADMIN = 'ADMIN'
    ROLE_DEVELOPER = 'DEVELOPER'
    ROLE_INVESTOR = 'INVESTOR'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DEVELOPER, 'Developer'),
        (ROLE_INVESTOR, 'Investor'),
    ]
    
    AUTH_LOCAL = 'LOCAL'
    AUTH_GOOGLE = 'GOOGLE'
    
    AUTH_PROVIDER_CHOICES = [
        (AUTH_LOCAL, 'Email/Password'),
        (AUTH_GOOGLE, 'Google OAuth'),
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
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_INVESTOR,
        db_index=True
    )
    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDER_CHOICES,
        default=AUTH_LOCAL
    )
    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['google_id']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_developer(self):
        return self.role == self.ROLE_DEVELOPER
    
    @property
    def is_investor(self):
        return self.role == self.ROLE_INVESTOR


class EmailVerificationToken(models.Model):
    """
    Email verification tokens.
    SRS: Email verification required before investing or accessing restricted data.
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
    token = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_used']),
        ]
    
    def __str__(self):
        return f"Verification token for {self.user.email}"


class PasswordResetToken(models.Model):
    """
    Password reset tokens.
    SRS: Users can reset password via email.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_used']),
        ]
    
    def __str__(self):
        return f"Reset token for {self.user.email}"