from rest_framework import generics, status, serializers
from drf_spectacular.utils import extend_schema, OpenApiExample
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
    UserProfileSerializer,
    TokenResponseSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer
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
from .permissions import IsAdmin
from utils.responses import success_response, error_response
from utils.exceptions import APIException
from apps.audit.services import log_admin_action


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
    
    @extend_schema(
        examples=[
            OpenApiExample(
                'Registration Success Example',
                value={
                    "success": True,
                    "message": "Registration successful. Please check your email to verify your account.",
                    "data": {
                        "email": "investor@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "role": "INVESTOR"
                    }
                },
                response_only=True,
            )
        ]
    )
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
    
    @extend_schema(
        responses=TokenResponseSerializer,
        examples=[
            OpenApiExample(
                'Login Success Example',
                value={
                    "success": True,
                    "message": "Login successful",
                    "data": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "email": "investor@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "role": "INVESTOR"
                        }
                    }
                },
                response_only=True,
            )
        ]
    )
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
    class LogoutSerializer(serializers.Serializer):
        refresh = serializers.CharField(help_text="Refresh token to blacklist")

    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get('refresh')
        
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
        
        return success_response(
            message="If an account with this email exists, a password reset link has been sent."
        )


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
    
    @extend_schema(responses=TokenResponseSerializer)
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


class AdminUserViewSet(generics.GenericAPIView):
    """
    ViewSet for Admin-only user management.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """List all users"""
        users = self.get_queryset()
        
        # Filtering
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)
            
        verified = request.query_params.get('is_email_verified')
        if verified is not None:
            users = users.filter(is_email_verified=verified.lower() == 'true')
            
        active = request.query_params.get('is_active')
        if active is not None:
            users = users.filter(is_active=active.lower() == 'true')
            
        # Pagination
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(users, many=True)
        return success_response(data=serializer.data)


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, or Delete user (Admin only).
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer
    
    def perform_destroy(self, instance):
        """Soft delete: deactivate user"""
        instance.is_active = False
        instance.save()
        log_admin_action(
            actor=self.request.user,
            action="USER_DEACTIVATED",
            entity_type="USER",
            entity_id=instance.id,
            metadata={"reason": "Admin soft delete"}
        )
        
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class AdminUserVerifyEmailView(generics.GenericAPIView):
    """
    Manually verify user email (Admin only).
    """
    queryset = User.objects.all()
    serializer_class = serializers.Serializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'id'
    
    def post(self, request, id):
        try:
            user = self.get_object()
            user.is_email_verified = True
            user.save()
            log_admin_action(
                actor=request.user,
                action="USER_EMAIL_VERIFIED_MANUALLY",
                entity_type="USER",
                entity_id=user.id
            )
            return success_response(message=f"Email for {user.email} verified.")
        except User.DoesNotExist:
            return error_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)


class AdminUserDeactivateView(generics.GenericAPIView):
    """
    Deactivate user (Admin only).
    """
    queryset = User.objects.all()
    serializer_class = serializers.Serializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'id'
    
    def post(self, request, id):
        try:
            user = self.get_object()
            user.is_active = False
            user.save()
            log_admin_action(
                actor=request.user,
                action="USER_DEACTIVATED_MANUALLY",
                entity_type="USER",
                entity_id=user.id
            )
            return success_response(message=f"User {user.email} deactivated.")
        except User.DoesNotExist:
            return error_response(message="User not found", status_code=status.HTTP_404_NOT_FOUND)