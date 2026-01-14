from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    Handles both regular and Google OAuth user creation.
    """
    
    def create_user(self, email, role, password=None, **extra_fields):
        """
        Create and save a regular user with email and password.
        """
        if not email:
            raise ValueError('Email address is required')
        
        if not role:
            raise ValueError('User role is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, role='ADMIN', password=None, **extra_fields):
        """
        Create and save a superuser with admin privileges.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, role, password, **extra_fields)
    
    def create_google_user(self, email, google_id, role, **extra_fields):
        """
        Create user from Google OAuth.
        Email is auto-verified for Google users.
        """
        extra_fields.setdefault('auth_method', 'GOOGLE')
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('is_active', True)
        
        user = self.create_user(
            email=email,
            role=role,
            password=None,
            **extra_fields
        )
        user.google_id = google_id
        user.save(using=self._db)
        
        return user