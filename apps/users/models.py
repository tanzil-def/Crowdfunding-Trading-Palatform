import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings


# ---------------- User Manager ----------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


# ---------------- Custom User Model ----------------
class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DEVELOPER = 'DEVELOPER', 'Project Developer'
        INVESTOR = 'INVESTOR', 'Investor'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.INVESTOR)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Tokens for email verification & password reset
    verification_token = models.UUIDField(null=True, blank=True, editable=False)
    verification_token_expiry = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False)
    password_reset_token_expiry = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # ---------------- Properties ----------------
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_developer(self):
        return self.role == self.Role.DEVELOPER

    @property
    def is_investor(self):
        return self.role == self.Role.INVESTOR

    def __str__(self):
        return self.email

    # ---------------- Token Generation ----------------
    def generate_verification_token(self):
        """Generates a new email verification token with expiry."""
        self.verification_token = uuid.uuid4()
        self.verification_token_expiry = timezone.now() + timedelta(
            minutes=getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES', 60)
        )
        self.save(update_fields=['verification_token', 'verification_token_expiry'])

    def generate_password_reset_token(self):
        """Generates a new password reset token with expiry."""
        self.password_reset_token = uuid.uuid4()
        self.password_reset_token_expiry = timezone.now() + timedelta(
            minutes=getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 60)
        )
        self.save(update_fields=['password_reset_token', 'password_reset_token_expiry'])
