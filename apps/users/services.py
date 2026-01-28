import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerificationToken, PasswordResetToken
from utils.exceptions import (
    AuthenticationFailedError, 
    UnverifiedUserError, 
    PermissionDeniedError,
    NotFoundError,
    ResourceConflictError
)


def generate_secure_token():
    """Generate a cryptographically secure token (Hex for better reliability)"""
    return secrets.token_hex(32)


def register_user(validated_data):
    """
    Register a new user and initiate email verification.
    SRS: Registration sends verification email.
    """
    if User.objects.filter(email=validated_data['email'].lower()).exists():
        raise ResourceConflictError("A user with this email already exists.")
    
    # Remove password_confirm if present (it's only for validation)
    validated_data.pop('password_confirm', None)
    
    user = User.objects.create_user(**validated_data)
    send_verification_email(user)
    return user


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
    Send verification email to user (HTML & Plain text).
    """
    token = create_verification_token(user)
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    
    subject = "Verify Your Email - Crowdfunding Platform"
    
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    context = {
        'first_name': user.first_name,
        'verification_url': verification_url,
        'expiry_minutes': settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES
    }
    
    html_message = render_to_string('emails/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
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
        raise NotFoundError("Invalid or expired verification token")
    
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
    """Send password reset email (HTML & Plain text)"""
    token = create_password_reset_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    
    subject = "Reset Your Password - Crowdfunding Platform"
    
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    context = {
        'first_name': user.first_name,
        'reset_url': reset_url,
        'expiry_minutes': settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
    }
    
    html_message = render_to_string('emails/password_reset_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
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
        raise NotFoundError("Invalid or expired reset token")
    
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
        raise AuthenticationFailedError("Invalid email or password")
    
    if not user.is_active:
        raise PermissionDeniedError("Account is inactive")
    
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


def logout_user(refresh_token):
    """
    Logout user by blacklisting refresh token.
    SRS: Secure logout with session invalidation.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        raise ValidationError("Invalid or already blacklisted token")


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
        raise AuthenticationFailedError(f"Google authentication failed: {str(e)}")