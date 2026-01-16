from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    GoogleOAuthSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer
)
from .services import (
    register_user,
    send_verification_email,
    verify_email_token,
    send_password_reset_email,
    reset_password_with_token,
    authenticate_user,
    generate_tokens_for_user,
    authenticate_google_oauth,
    logout_user
)
from utils.responses import success_response, error_response
from utils.exceptions import APIException


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    
    Register new user (Developer or Investor).
    
    SRS Requirements:
    - Email, password, first_name, last_name required
    - Role selection (DEVELOPER or INVESTOR only)
    - Email verification sent after registration
    - Admin users created via backend only
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = register_user(serializer.validated_data)
            
            return success_response(
                data={
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role
                },
                message="Registration successful. Please check your email to verify your account.",
                status_code=status.HTTP_201_CREATED
            )
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class UserLoginView(generics.GenericAPIView):
    """
    POST /api/v1/auth/login/
    
    Login with email and password.
    
    SRS Requirements:
    - Email and password authentication
    - Returns JWT access and refresh tokens
    - Works for all roles (Admin, Developer, Investor)
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = authenticate_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            tokens = generate_tokens_for_user(user)
            
            return success_response(
                data={
                    "access": tokens['access'],
                    "refresh": tokens['refresh']
                },
                message="Login successful"
            )
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class UserLogoutView(generics.GenericAPIView):
    """
    POST /api/v1/auth/logout/
    
    Logout user by blacklisting refresh token.
    
    SRS Requirements:
    - Secure logout
    - Session invalidation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return error_response(
                message="Refresh token required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            logout_user(refresh_token)
            return success_response(message="Logout successful")
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class EmailVerificationView(generics.GenericAPIView):
    """
    POST /api/v1/auth/verify-email/
    
    Verify email using token sent via email.
    
    SRS Requirements:
    - Email verification required
    - Enables investment and restricted access features
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = verify_email_token(serializer.validated_data['token'])
            
            return success_response(
                data={
                    "email": user.email,
                    "is_verified": user.is_email_verified
                },
                message="Email verified successfully"
            )
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/
    
    Request password reset via email.
    
    SRS Requirements:
    - Users can reset password
    - Reset link sent via email
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email'].lower()
        
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass
        
        return Response({
            "success": True,
            "message": "If an account with this email exists, a password reset link has been sent."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset-confirm/
    
    Confirm password reset with token and new password.
    
    SRS Requirements:
    - Secure password reset
    - Token validation
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = reset_password_with_token(
                token_str=serializer.validated_data['token'],
                new_password=serializer.validated_data['password']
            )
            
            return success_response(
                message="Password reset successful. You can now login with your new password."
            )
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class GoogleOAuthView(generics.GenericAPIView):
    """
    POST /api/v1/auth/google/
    
    Authenticate via Google OAuth.
    
    SRS Requirements:
    - OAuth support
    - Auto email verification
    - Returns JWT tokens
    """
    serializer_class = GoogleOAuthSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = authenticate_google_oauth(
                google_token=serializer.validated_data['token'],
                role=serializer.validated_data.get('role', User.ROLE_INVESTOR)
            )
            
            tokens = generate_tokens_for_user(user)
            
            return success_response(
                data={
                    "access": tokens['access'],
                    "refresh": tokens['refresh']
                },
                message="Google authentication successful"
            )
        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            return error_response(
                message=str(detail),
                status_code=status_code
            )


class UserProfileView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/profile/
    
    Get authenticated user's profile.
    
    SRS Requirements:
    - View own profile
    - Shows role and verification status
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user