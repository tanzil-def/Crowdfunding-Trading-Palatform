import uuid
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

# Temp token storage for demo purposes
EMAIL_VERIFICATION_TOKENS = {}
PASSWORD_RESET_TOKENS = {}

# -------------------------------
# REGISTER
# -------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        self._send_verification_email(user)

    def _send_verification_email(self, user):
        token = str(uuid.uuid4())
        expiry = timezone.now() + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES)
        user.verification_token = token
        user.verification_token_expiry = expiry
        user.save()

        verification_url = f"http://{settings.FRONTEND_URL}/verify-email/?token={token}&email={user.email}"

        send_mail(
            subject="Verify Your Email - Crowdfunding Platform",
            message=f"Click to verify: {verification_url}\nExpires in 60 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

# -------------------------------
# LOGIN
# -------------------------------
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(email=serializer.validated_data['email'], password=serializer.validated_data['password'])
        if not user:
            return Response({"success": False, "error":{"code":"INVALID_CREDENTIALS","message":"Invalid credentials"}}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_email_verified:
            return Response({"success": False, "error":{"code":"EMAIL_NOT_VERIFIED","message":"Email not verified"}}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "message": "Login successful",
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            }
        })

# -------------------------------
# LOGOUT
# -------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"success": False, "error": {"code": "NO_TOKEN_PROVIDED", "message": "Refresh token is required"}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the refresh token
            return Response({"success": True, "message": "Logout successful"})
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "INVALID_TOKEN", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )

# -------------------------------
# EMAIL VERIFICATION
# -------------------------------
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        email = EMAIL_VERIFICATION_TOKENS.pop(token, None)
        if not email:
            return Response({"success": False,"error":{"code":"INVALID_TOKEN","message":"Invalid token"}}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        user.is_email_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        user.save()
        return Response({"success": True,"message":"Email verified successfully"})

# -------------------------------
# PASSWORD RESET
# -------------------------------
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user:
            token = str(uuid.uuid4())
            PASSWORD_RESET_TOKENS[token] = user.email
            send_mail(
                subject="Password Reset Request",
                message=f"Reset your password: http://{settings.FRONTEND_URL}/reset-password/?token={token}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )
        return Response({"success": True,"message":"If email exists, password reset link sent."})

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        email = PASSWORD_RESET_TOKENS.pop(token, None)
        if not email:
            return Response({"success": False, "error":{"code":"INVALID_TOKEN","message":"Invalid token"}}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response({"success": True,"message":"Password reset successful"})
