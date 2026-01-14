import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerificationToken, PasswordResetToken


def generate_secure_token():
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(48)


def create_verification_token(user):
    """
    Create email verification token.
    SRS: Email verification required.
    """
    token_str = generate_secure_token()
    expires_at = timezone.now() + timedelta(
        minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES
    )
    
    token = EmailVerificationToken.objects.create(
        user=user,
        token=token_str,
        expires_at=expires_at
    )
    
    return token


def send_verification_email(user):
    """
    Send verification email to user.
    """
    token = create_verification_token(user)
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    
    subject = "Verify Your Email - Crowdfunding Platform"
    message = f"""
Hi {user.first_name},

Welcome to Crowdfunding Platform!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES} minutes.

If you did not create this account, please ignore this email.

Best regards,
Crowdfunding Platform Team
    """.strip()
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )


def verify_email_token(token_str):
    """
    Verify email using token.
    SRS: Email verification enforcement.
    """
    try:
        token = EmailVerificationToken.objects.get(
            token=token_str,
            is_used=False
        )
    except EmailVerificationToken.DoesNotExist:
        raise ValidationError("Invalid or expired verification token")
    
    if token.expires_at < timezone.now():
        raise ValidationError("Verification token has expired")
    
    token.is_used = True
    token.save(update_fields=['is_used'])
    
    user = token.user
    user.is_email_verified = True
    user.save(update_fields=['is_email_verified'])
    
    return user


def create_password_reset_token(user):
    """Create password reset token"""
    token_str = generate_secure_token()
    expires_at = timezone.now() + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
    )
    
    token = PasswordResetToken.objects.create(
        user=user,
        token=token_str,
        expires_at=expires_at
    )
    
    return token


def send_password_reset_email(user):
    """Send password reset email"""
    token = create_password_reset_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    
    subject = "Reset Your Password - Crowdfunding Platform"
    message = f"""
Hi {user.first_name},

We received a request to reset your password.

Click the link below to reset your password:
{reset_url}

This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES} minutes.

If you did not request this password reset, please ignore this email.

Best regards,
Crowdfunding Platform Team
    """.strip()
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )


def reset_password_with_token(token_str, new_password):
    """Reset password using token"""
    try:
        token = PasswordResetToken.objects.get(
            token=token_str,
            is_used=False
        )
    except PasswordResetToken.DoesNotExist:
        raise ValidationError("Invalid or expired reset token")
    
    if token.expires_at < timezone.now():
        raise ValidationError("Reset token has expired")
    
    token.is_used = True
    token.save(update_fields=['is_used'])
    
    user = token.user
    user.set_password(new_password)
    user.save(update_fields=['password'])
    
    return user


def authenticate_user(email, password):
    """
    Authenticate user with email and password.
    SRS: Login with email and password.
    """
    user = authenticate(username=email.lower(), password=password)
    
    if not user:
        raise ValidationError("Invalid email or password")
    
    if not user.is_active:
        raise ValidationError("Account is inactive")
    
    return user


def generate_tokens_for_user(user):
    """
    Generate JWT tokens for user.
    SRS: Return access and refresh tokens.
    """
    refresh = RefreshToken.for_user(user)
    
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


def authenticate_google_oauth(google_token, role=User.ROLE_INVESTOR):
    """
    Authenticate or create user via Google OAuth.
    SRS: Support OAuth authentication.
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        idinfo = id_token.verify_oauth2_token(
            google_token,
            requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValidationError("Invalid token issuer")
        
        google_id = idinfo['sub']
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        if not email:
            raise ValidationError("Email not provided by Google")
        
        try:
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=email.lower())
                user.google_id = google_id
                user.auth_provider = User.AUTH_GOOGLE
                user.is_email_verified = True
                user.save(update_fields=['google_id', 'auth_provider', 'is_email_verified'])
            except User.DoesNotExist:
                user = User.objects.create_oauth_user(
                    email=email,
                    first_name=first_name or email.split('@')[0],
                    last_name=last_name or '',
                    google_id=google_id,
                    role=role
                )
        
        return user
        
    except Exception as e:
        raise ValidationError(f"Google authentication failed: {str(e)}")