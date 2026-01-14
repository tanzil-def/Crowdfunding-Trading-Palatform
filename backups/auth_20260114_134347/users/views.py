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
    send_verification_email,
    verify_email_token,
    send_password_reset_email,
    reset_password_with_token,
    authenticate_user,
    generate_tokens_for_user,
    authenticate_google_oauth
)


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
        user = serializer.save()
        
        send_verification_email(user)
        
        return Response({
            "success": True,
            "message": "Registration successful. Please check your email to verify your account.",
            "data": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
        }, status=status.HTTP_201_CREATED)


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
        
        user = authenticate_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        tokens = generate_tokens_for_user(user)
        
        return Response({
            "success": True,
            "message": "Login successful",
            "data": {
                "access": tokens['access'],
                "refresh": tokens['refresh']
            }
        }, status=status.HTTP_200_OK)


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
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": "Refresh token required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "success": True,
                "message": "Logout successful"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "Invalid token"
            }, status=status.HTTP_400_BAD_REQUEST)


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
            
            return Response({
                "success": True,
                "message": "Email verified successfully",
                "data": {
                    "email": user.email,
                    "is_verified": user.is_email_verified
                }
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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
            
            return Response({
                "success": True,
                "message": "Password reset successful. You can now login with your new password."
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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
            
            return Response({
                "success": True,
                "message": "Google authentication successful",
                "data": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh']
                }
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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