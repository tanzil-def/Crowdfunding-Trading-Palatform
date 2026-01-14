import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import EmailVerificationToken, PasswordResetToken, User


def generate_token():
    """Generate secure random token."""
    return secrets.token_urlsafe(32)


def create_email_verification_token(user):
    """
    Create email verification token for user.
    SRS Requirement: Email verification tokens expire after configured time.
    """
    token = generate_token()
    expiry_minutes = getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES', 30)
    
    verification_token = EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
    )
    
    return verification_token


def create_password_reset_token(user):
    """
    Create password reset token for user.
    SRS Requirement: Password reset tokens expire after configured time.
    """
    token = generate_token()
    expiry_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 15)
    
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
    )
    
    return reset_token


def send_verification_email(user, verification_token):
    """
    Send email verification link to user.
    SRS Requirement: Email verification via email link.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verification_url = f"{frontend_url}/verify-email?token={verification_token.token}"
    
    subject = 'Verify Your Email - Crowdfunding Platform'
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'expiry_minutes': getattr(settings, 'EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES', 30)
    }
    
    message = render_to_string('emails/verify_email.txt', context)
    html_message = render_to_string('emails/verify_email.html', context)
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )


def send_password_reset_email(user, reset_token):
    """
    Send password reset link to user.
    SRS Requirement: Password reset via email.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={reset_token.token}"
    
    subject = 'Reset Your Password - Crowdfunding Platform'
    
    context = {
        'user': user,
        'reset_url': reset_url,
        'expiry_minutes': getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 15)
    }
    
    message = render_to_string('emails/password_reset.txt', context)
    html_message = render_to_string('emails/password_reset.html', context)
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )


def verify_email_token(token_string):
    """
    Verify email verification token and mark user as verified.
    """
    try:
        token = EmailVerificationToken.objects.get(token=token_string)
        
        if not token.is_valid:
            return None, "Token has expired or already been used."
        
        user = token.user
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        
        token.is_used = True
        token.save(update_fields=['is_used'])
        
        return user, None
        
    except EmailVerificationToken.DoesNotExist:
        return None, "Invalid verification token."


def verify_password_reset_token(token_string):
    """
    Verify password reset token.
    Returns user if valid, None otherwise.
    """
    try:
        token = PasswordResetToken.objects.get(token=token_string)
        
        if not token.is_valid:
            return None, "Token has expired or already been used."
        
        return token.user, None
        
    except PasswordResetToken.DoesNotExist:
        return None, "Invalid reset token."


def confirm_password_reset(token_string, new_password):
    """
    Confirm password reset and update user password.
    """
    user, error = verify_password_reset_token(token_string)
    
    if error:
        return None, error
    
    try:
        token = PasswordResetToken.objects.get(token=token_string)
        
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        token.is_used = True
        token.save(update_fields=['is_used'])
        
        return user, None
        
    except PasswordResetToken.DoesNotExist:
        return None, "Invalid reset token."


def cleanup_expired_tokens():
    """
    Clean up expired verification and reset tokens.
    Can be run as a periodic task (Celery).
    """
    now = timezone.now()
    
    EmailVerificationToken.objects.filter(
        expires_at__lt=now,
        is_used=False
    ).delete()
    
    PasswordResetToken.objects.filter(
        expires_at__lt=now,
        is_used=False
    ).delete()