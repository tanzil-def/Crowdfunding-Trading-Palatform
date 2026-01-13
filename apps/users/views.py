import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    LogoutSerializer
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        self.send_verification_email(user)
        self.user = user

    def send_verification_email(self, user):
        token = str(uuid.uuid4())
        user.verification_token = token
        user.verification_token_expiry = timezone.now() + timedelta(
            minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES
        )
        user.save()

        verify_url = f"{settings.FRONTEND_URL}/verify-email/?token={token}"

        send_mail(
            subject="Welcome to Crowdfunding Platform – Verify Your Email",
            message=f"""
Hi {user.name},

Welcome to Crowdfunding Platform 🎉

Please verify your email to activate your account:
{verify_url}

This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES} minutes.

Thanks,
Crowdfunding Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        
        return Response(
            {
                "success": True,
                "message": "Registration successful. Verification email sent.",
                "data": {
                    "name": self.user.name,
                    "email": self.user.email,
                    "role": self.user.role,
                    "verification_token": self.user.verification_token
                }
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )

        if not user:
            return Response(
                {"success": False, "error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_email_verified:
            return Response(
                {"success": False, "error": "Email not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            return Response(
                {"success": True, "message": "Logout successful"}
            )
        except Exception:
            return Response(
                {"success": False, "error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailVerificationSerializer,
        responses={200: {"type": "object", "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"}
        }}},
        examples=[
            OpenApiExample(
                'Verify Email Request',
                value={"token": "dd97b1a1-dffc-4853-baa9-a8a9870e16f8"},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(
            User,
            verification_token=serializer.validated_data['token']
        )

        if user.verification_token_expiry < timezone.now():
            return Response(
                {"success": False, "error": "Token expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_email_verified = True
        user.verification_token = None
        user.verification_token_expiry = None
        user.save()

        return Response(
            {"success": True, "message": "Email verified successfully"}
        )


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data['email']).first()
        token = None
        
        if user:
            token = str(uuid.uuid4())
            user.password_reset_token = token
            user.password_reset_token_expiry = timezone.now() + timedelta(
                minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
            )
            user.save()

            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={token}"

            send_mail(
                subject="Reset Your Crowdfunding Account Password",
                message=f"""
Hi {user.name},

We received a password reset request for your Crowdfunding Platform account.

Click below to reset your password:
{reset_url}

If you didn't request this, ignore this email.

Thanks,
Crowdfunding Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )

        return Response(
            {
                "success": True,
                "message": "If email exists, password reset link sent.",
                "token": token
            }
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(
            User,
            password_reset_token=serializer.validated_data['token']
        )

        if user.password_reset_token_expiry < timezone.now():
            return Response(
                {"success": False, "error": "Token expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['password'])
        user.password_reset_token = None
        user.password_reset_token_expiry = None
        user.save()

        return Response(
            {"success": True, "message": "Password reset successful"}
        )