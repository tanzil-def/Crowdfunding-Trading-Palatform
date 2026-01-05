# apps/users/views.py
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from uuid import uuid4
from datetime import timedelta

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    inline_serializer,
)
from rest_framework import serializers as drf_serializers

from .models import CustomUser
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)


# Helper method (add to model or here)
def generate_token(user):
    token = uuid4()
    expiry = timezone.now() + timedelta(minutes=60)
    user.verification_token = token
    user.verification_token_expiry = expiry
    user.save(update_fields=['verification_token', 'verification_token_expiry'])
    return token


# ---------------- REGISTER ----------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register as Investor or Developer",
        request=RegisterSerializer,
        responses={201: inline_serializer("RegisterSuccess", fields={
            "success": drf_serializers.BooleanField(),
            "message": drf_serializers.CharField(),
            "user": UserSerializer,
        })}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = generate_token(user)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}"

        send_mail(
            subject="Verify Your Crowdfunding Account",
            message=f"Click to verify: {verification_url}\nLink expires in 60 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({
            "success": True,
            "message": "Registration successful. Please check your email to verify your account.",
            "user": UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


# ---------------- LOGIN ----------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="User Login", request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = CustomUser.objects.get(email__iexact=serializer.validated_data["email"])
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid email or password"}, status=401)

        if not user.check_password(serializer.validated_data["password"]):
            return Response({"success": False, "message": "Invalid email or password"}, status=401)

        if not user.is_active:
            return Response({"success": False, "message": "Account disabled"}, status=403)

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
            "user": UserSerializer(user).data,
            "next_action": "VERIFY_EMAIL" if not user.is_verified else "DASHBOARD",
        })


# ---------------- LOGOUT ----------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Fixes drf-spectacular warning

    @extend_schema(summary="Logout (All Devices)")
    def post(self, request):
        try:
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
            return Response({"success": True, "message": "Logged out successfully from all devices"})
        except Exception:
            return Response({"success": False, "message": "Logout failed"}, status=400)


# ---------------- VERIFY EMAIL ----------------
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Email",
        parameters=[
            OpenApiParameter(name="email", type=str, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="token", type=str, location=OpenApiParameter.QUERY, required=True),
        ]
    )
    def get(self, request):
        token = request.query_params.get("token")
        email = request.query_params.get("email")

        if not token or not email:
            return Response({"success": False, "message": "Email and token required"}, status=400)

        try:
            user = CustomUser.objects.get(email__iexact=email, verification_token=token)
            if user.verification_token_expiry < timezone.now():
                return Response({"success": False, "message": "Token expired"}, status=400)

            user.is_verified = True
            user.verification_token = None
            user.verification_token_expiry = None
            user.save()

            return Response({"success": True, "message": "Email verified successfully"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid token"}, status=400)


# ---------------- RESEND VERIFICATION ----------------
class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Resend Verification Email")
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"success": False, "message": "Email required"}, status=400)

        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.is_verified:
                return Response({"success": False, "message": "Already verified"}, status=400)

            token = generate_token(user)
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}"

            send_mail(
                subject="Resend: Verify Your Email",
                message=f"Click to verify: {verification_url}\nExpires in 60 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return Response({"success": True, "message": "Verification email resent"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)


# ---------------- PASSWORD RESET ----------------
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Request Password Reset", request=PasswordResetSerializer)
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = CustomUser.objects.get(email__iexact=email)
            token = uuid4()
            expiry = timezone.now() + timedelta(minutes=60)
            user.password_reset_token = token
            user.password_reset_token_expiry = expiry
            user.save()

            reset_url = f"{settings.FRONTEND_URL}/reset-password-confirm?token={token}&email={user.email}"
            send_mail(
                subject="Password Reset",
                message=f"Click to reset: {reset_url}\nExpires in 60 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except CustomUser.DoesNotExist:
            pass  # Security: don't reveal if email exists

        return Response({"success": True, "message": "Password reset email sent if account exists"})


# ---------------- PASSWORD RESET CONFIRM ----------------
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Confirm Password Reset", request=PasswordResetConfirmSerializer)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = CustomUser.objects.get(email__iexact=email, password_reset_token=token)
            if user.password_reset_token_expiry < timezone.now():
                return Response({"success": False, "message": "Token expired"}, status=400)

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_expiry = None
            user.save()

            return Response({"success": True, "message": "Password reset successful"})
        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid token"}, status=400)