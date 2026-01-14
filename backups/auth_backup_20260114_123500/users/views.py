from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    GoogleOAuthSerializer,
    LoginSerializer,
    EmailVerificationSerializer,
    ResendVerificationEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer
)
from .services import (
    create_email_verification_token,
    create_password_reset_token,
    send_verification_email,
    send_password_reset_email,
    verify_email_token,
    confirm_password_reset
)
from utils.responses import success_response, error_response


def get_tokens_for_user(user):
    """Generate JWT tokens for user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserRegistrationView(generics.GenericAPIView):
    """
    POST /api/v1/auth/register/
    
    Register new user with email and password.
    SRS Requirement: User registration with role selection.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        verification_token = create_email_verification_token(user)
        send_verification_email(user, verification_token)
        
        return success_response(
            data={
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role
            },
            message="Registration successful. Please check your email to verify your account.",
            status_code=status.HTTP_201_CREATED
        )


class GoogleOAuthLoginView(generics.GenericAPIView):
    """
    POST /api/v1/auth/google/
    
    Login or register using Google OAuth.
    Verifies Google ID token and creates/updates user.
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleOAuthSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        
        return success_response(
            data={
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            },
            message="Google authentication successful"
        )


class LoginView(generics.GenericAPIView):
    """
    POST /api/v1/auth/login/
    
    Login with email and password.
    SRS Requirement: Secure login functionality.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return success_response(
            data={
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            },
            message="Login successful"
        )


class LogoutView(generics.GenericAPIView):
    """
    POST /api/v1/auth/logout/
    
    Logout user and blacklist refresh token.
    SRS Requirement: Secure logout functionality.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return success_response(
                message="Logout successful"
            )
        except Exception:
            return error_response(
                message="Invalid token",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(generics.GenericAPIView):
    """
    POST /api/v1/auth/verify-email/
    
    Verify user email with token.
    SRS Requirement: Email verification required.
    """
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        user, error = verify_email_token(token)
        
        if error:
            return error_response(
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return success_response(
            data={
                'email': user.email,
                'is_verified': user.is_email_verified
            },
            message="Email verified successfully"
        )


class ResendVerificationEmailView(generics.GenericAPIView):
    """
    POST /api/v1/auth/resend-verification/
    
    Resend verification email to user.
    """
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationEmailSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['email']
        
        verification_token = create_email_verification_token(user)
        send_verification_email(user, verification_token)
        
        return success_response(
            message="Verification email sent successfully"
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/
    
    Request password reset email.
    SRS Requirement: Password reset via email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['email']
        
        if user:
            reset_token = create_password_reset_token(user)
            send_password_reset_email(user, reset_token)
        
        return success_response(
            message="If an account exists with this email, a password reset link has been sent."
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset-confirm/
    
    Confirm password reset with token and new password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['password']
        
        user, error = confirm_password_reset(token, new_password)
        
        if error:
            return error_response(
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return success_response(
            message="Password reset successful. You can now login with your new password."
        )


class UserProfileView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/profile/
    
    Get authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/auth/profile/update/
    
    Update user profile information.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return success_response(
            data=UserProfileSerializer(instance).data,
            message="Profile updated successfully"
        )


class ChangePasswordView(generics.GenericAPIView):
    """
    POST /api/v1/auth/change-password/
    
    Change password for authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        update_session_auth_hash(request, user)
        
        return success_response(
            message="Password changed successfully"
        )


class TokenRefreshAPIView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/
    
    Refresh access token using refresh token.
    """
    pass