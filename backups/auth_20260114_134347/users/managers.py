from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for User model.
    Handles creation of regular users and superusers.
    """
    
    def _validate_email(self, email):
        """Validate email format"""
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Invalid email address")
        return email.lower()
    
    def create_user(self, email, password, first_name, last_name, role='INVESTOR', **extra_fields):
        """
        Create and save a regular user.
        """
        if not email:
            raise ValueError("Email address is required")
        if not first_name:
            raise ValueError("First name is required")
        if not last_name:
            raise ValueError("Last name is required")
        
        email = self._validate_email(email)
        
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, first_name='Admin', last_name='User', **extra_fields):
        """
        Create and save a superuser (Admin role).
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
    
    def create_oauth_user(self, email, first_name, last_name, google_id, role='INVESTOR'):
        """
        Create user via Google OAuth.
        Email is automatically verified for OAuth users.
        """
        email = self._validate_email(email)
        
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            auth_provider='GOOGLE',
            google_id=google_id,
            is_email_verified=True,
            is_active=True
        )
        
        user.set_unusable_password()
        user.save(using=self._db)
        return user