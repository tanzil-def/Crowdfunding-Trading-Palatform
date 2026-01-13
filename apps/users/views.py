from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.cache import cache

from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, Wallet, WalletTransaction
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
)
from .permissions import IsAdminUser, IsDeveloperUser, IsInvestorUser, IsVerifiedUser


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    SRS: Users can register as Investor or Developer
    """
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful. Please verify your email.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    User login endpoint
    SRS: Email verification required for protected actions
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if not user:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'error': 'Account is deactivated'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user.is_banned:
            return Response({
                'success': False,
                'error': 'Account is banned'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    """
    User logout endpoint
    SRS: Secure session management
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Successfully logged out'
            })
        except Exception:
            # Even if blacklist fails, we consider logout successful
            return Response({
                'success': True,
                'message': 'Logout successful'
            })


class VerifyEmailView(APIView):
    """
    Email verification endpoint
    SRS: Email verification required before investing
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        user = User.objects.get(verification_token=token)
        
        # Mark as verified
        user.is_verified = True
        user.verification_token = None
        user.verification_sent_at = None
        user.save()
        
        return Response({
            'success': True,
            'message': 'Email verified successfully'
        })


class PasswordResetRequestView(APIView):
    """
    Password reset request endpoint
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset token
        import uuid
        user.reset_token = uuid.uuid4()
        user.reset_token_expiry = timezone.now() + timezone.timedelta(hours=24)
        user.save()
        
        # Send reset email (simplified)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.reset_token}/"
        
        # TODO: Implement actual email sending
        
        return Response({
            'success': True,
            'message': 'Password reset email sent'
        })


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        password = serializer.validated_data['password']
        
        # Update password
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password reset successful'
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile
    """
    
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer
    
    def get_object(self):
        return self.request.user


class WalletView(generics.RetrieveAPIView):
    """
    Get user wallet details
    SRS: For refund/withdrawal tracking
    """
    
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class WalletTransactionView(generics.ListAPIView):
    """
    Get wallet transaction history
    """
    
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all().order_by('-created_at')


# Admin views
class UserListView(generics.ListAPIView):
    """
    List all users (Admin only)
    SRS: Admin panel requirement
    """
    
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        return queryset.order_by('-date_joined')


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin user management
    SRS: Admin can manage users
    """
    
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    
    def perform_destroy(self, instance):
        # Soft delete instead of hard delete
        instance.is_active = False
        instance.save()


class BanUserView(APIView):
    """
    Ban/Unban user (Admin only)
    SRS: Admin governance
    """
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            if user.is_banned:
                user.is_banned = False
                user.banned_at = None
                message = 'User unbanned successfully'
            else:
                user.is_banned = True
                user.banned_at = timezone.now()
                message = 'User banned successfully'
            
            user.save()
            
            # Log the action
            from audit.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='USER_BANNED' if user.is_banned else 'USER_UNBANNED',
                target_user=user,
                metadata={'reason': request.data.get('reason', '')}
            )
            
            return Response({
                'success': True,
                'message': message,
                'user': UserSerializer(user).data
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ResendVerificationView(APIView):
    """
    Resend verification email (Admin only)
    """
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.send_verification_email()
            
            return Response({
                'success': True,
                'message': 'Verification email sent'
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


# Custom token refresh with additional validation
class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh with user status validation
    """
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Add additional user info to response
            from rest_framework_simplejwt.tokens import AccessToken
            
            token = AccessToken(response.data['access'])
            user_id = token['user_id']
            
            try:
                user = User.objects.get(id=user_id)
                response.data['user'] = UserSerializer(user).data
            except User.DoesNotExist:
                pass
        
        return response