import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    """Custom User Manager"""

    def create_user(self, email, role='INVESTOR', password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, role='ADMIN', password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with roles, email verification, and password reset"""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DEVELOPER = 'DEVELOPER', 'Developer'
        INVESTOR = 'INVESTOR', 'Investor'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.INVESTOR)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    # Email verification fields
    verification_token = models.CharField(max_length=255, null=True, blank=True)
    verification_token_expiry = models.DateTimeField(null=True, blank=True)

    # Password reset fields
    password_reset_token = models.CharField(max_length=255, null=True, blank=True)
    password_reset_token_expiry = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_developer(self):
        return self.role == self.Role.DEVELOPER

    @property
    def is_investor(self):
        return self.role == self.Role.INVESTOR
