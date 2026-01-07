import uuid
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,  
    inline_serializer,
)
from rest_framework import serializers  # inline_serializer er jonno

from .models import CustomUser
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import uuid

from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .permissions import IsVerified

# Token storage (replace with DB or JWT-signed in prod)
EMAIL_VERIFICATION_TOKENS = {}
PASSWORD_RESET_TOKENS = {}
# -------------------------------
# REGISTER
# -------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register new user (Investor or Developer)",
        description="Creates a new user and sends email verification link. Role must be 'INVESTOR' or 'DEVELOPER'.",
        request=RegisterSerializer,
        responses={201: UserSerializer},
        examples=[
            OpenApiExample("Investor Registration", value={"email": "investor@example.com", "role": "INVESTOR", "password": "StrongPass123!", "password2": "StrongPass123!"}),
            OpenApiExample("Developer Registration", value={"email": "developer@example.com", "role": "DEVELOPER", "password": "StrongPass123!", "password2": "StrongPass123!"}),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()
        self._send_verification_email(user)

    def _send_verification_email(self, user):
        token = uuid.uuid4()
        expiry = timezone.now() + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES)
        user.verification_token = token
        user.verification_token_expiry = expiry
        user.save()

        verification_url = f"http://{settings.SITE_DOMAIN}{reverse('verify-email')}?token={token}&email={user.email}"

        send_mail(
            subject="Verify Your Email - Crowdfunding Platform",
            message=f"Welcome!\n\nClick to verify: {verification_url}\n\nExpires in 60 minutes.",
            from_email="no-reply@crowdfundingplatform.com",
            recipient_list=[user.email],
            fail_silently=False,
        )


# -------------------------------
# LOGIN
# -------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login and return JWT tokens",
        description="Authenticates user. If not verified, frontend should prompt verification.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="LoginResponse",
                    fields={
                        "success": serializers.BooleanField(),
                        "tokens": serializers.DictField(),
                        "user": UserSerializer(),
                        "next_action": serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample("Verified Login", value={
                        "success": True,
                        "tokens": {"refresh": "ey...", "access": "ey..."},
                        "user": {"email": "a@b.com", "role": "INVESTOR", "is_verified": True},
                        "next_action": "DASHBOARD"
                    }),
                    OpenApiExample("Unverified Login", value={
                        "success": True,
                        "tokens": {"refresh": "ey...", "access": "ey..."},
                        "user": {"email": "a@b.com", "role": "DEVELOPER", "is_verified": False},
                        "next_action": "VERIFY_EMAIL"
                    }),
                ]
            )
        },
        examples=[OpenApiExample("Login Request", value={"email": "user@example.com", "password": "StrongPass123!"})],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"success": False, "message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"success": False, "message": "Account disabled"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "user": UserSerializer(user).data,
            "next_action": "VERIFY_EMAIL" if not user.is_verified else "DASHBOARD",
        })


# -------------------------------
# VERIFY EMAIL
# -------------------------------
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify email using token",
        parameters=[
            OpenApiParameter(name="token", type=str, location=OpenApiParameter.QUERY, required=True, description="Verification token"),
            OpenApiParameter(name="email", type=str, location=OpenApiParameter.QUERY, required=True, description="User email"),
        ],
        responses={200: {"success": True, "message": "Email verified successfully"}},
    )
    def get(self, request):
        token = request.query_params.get("token")
        email = request.query_params.get("email")

        if not token or not email:
            return Response({"success": False, "message": "Token and email required"}, status=400)

        try:
            user = CustomUser.objects.get(email=email, verification_token=token)
            if user.verification_token_expiry < timezone.now():
                return Response({"success": False, "message": "Token expired"}, status=400)

            user.is_verified = True
            user.verification_token = None
            user.verification_token_expiry = None
            user.save()

            return Response({"success": True, "message": "Email verified successfully"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid token or email"}, status=400)


# -------------------------------
# RESEND VERIFICATION
# -------------------------------
class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend verification email",
        request=inline_serializer(name="ResendEmail", fields={"email": serializers.EmailField()}),
        responses={200: {"success": True, "message": "Verification email resent"}},
    )
    

    def perform_create(self, serializer):
        user = serializer.save()
        token = str(uuid.uuid4())
        EMAIL_VERIFICATION_TOKENS[token] = user.email
        send_mail(
            subject="Welcome! Verify your email",
            message=f"Hello {user.name}, verify your email: http://localhost:3000/verify-email/?token={token}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Registration successful. Verification email sent.",
            "data": resp.data
        })

class VerifyEmailView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        email = EMAIL_VERIFICATION_TOKENS.pop(token, None)
        if not email:
            return Response({
                "success": False,
                "error": {"code": "INVALID_TOKEN","message":"Invalid token"}
            }, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        user.is_email_verified = True
        user.save()
        return Response({"success": True,"message":"Email verified successfully"})
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_verified:
                return Response({"success": False, "message": "Already verified"}, status=400)

            token = uuid.uuid4()
            expiry = timezone.now() + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES)
            user.verification_token = token
            user.verification_token_expiry = expiry
            user.save()

            verification_url = f"http://{settings.SITE_DOMAIN}{reverse('verify-email')}?token={token}&email={user.email}"
            send_mail(
                subject="Resend: Verify Your Email",
                message=f"Click to verify:\n{verification_url}",
                from_email="no-reply@crowdfundingplatform.com",
                recipient_list=[user.email],
            )

            return Response({"success": True, "message": "Verification email resent"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)
        
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(email=serializer.validated_data['email'], password=serializer.validated_data['password'])
        if not user:
            return Response({"success": False,"error":{"code":"INVALID_CREDENTIALS","message":"Invalid credentials"}}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_email_verified:
            return Response({"success": False,"error":{"code":"EMAIL_NOT_VERIFIED","message":"Email not verified"}}, status=status.HTTP_403_FORBIDDEN)
        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "message": "Login successful",
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            }
        })

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"success": True,"message":"Logged out successfully"})

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
                message=f"Hello {user.name}, reset your password: http://localhost:3000/reset-password/?token={token}",
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
            return Response({
                "success": False,
                "error": {"code":"INVALID_TOKEN","message":"Invalid token"}
            }, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response({"success": True,"message":"Password reset successful"})
