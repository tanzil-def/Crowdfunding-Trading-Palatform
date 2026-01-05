from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import status, serializers
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

from .models import CustomUser
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)


# ---------------- REGISTER ----------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register as Investor or Developer",
        description=(
            "Creates a new user account. Only INVESTOR or DEVELOPER roles are allowed. "
            "Admin registration is blocked. Sends email verification link automatically."
        ),
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                name="RegisterSuccessResponse",
                fields={
                    "success": serializers.BooleanField(default=True),
                    "message": serializers.CharField(),
                    "user": inline_serializer(
                        name="RegisteredUser",
                        fields={
                            "email": serializers.EmailField(),
                            "role": serializers.ChoiceField(choices=["INVESTOR", "DEVELOPER"]),
                            "is_verified": serializers.BooleanField(default=False),
                        },
                    ),
                },
            )
        },
        examples=[
            OpenApiExample(
                "Register as Investor",
                value={
                    "email": "investor@example.com",
                    "role": "INVESTOR",
                    "password": "MyStrongPass123!",
                    "password2": "MyStrongPass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register as Developer",
                value={
                    "email": "developer@example.com",
                    "role": "DEVELOPER",
                    "password": "MyStrongPass123!",
                    "password2": "MyStrongPass123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Successful Registration Response",
                value={
                    "success": True,
                    "message": "Registration successful. Please check your email to verify your account.",
                    "user": {
                        "email": "investor@example.com",
                        "role": "INVESTOR",
                        "is_verified": False,
                    },
                },
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.verification_token}&email={user.email}"

        send_mail(
            subject="Verify Your Crowdfunding Account",
            message=(
                f"Hello {user.email},\n\n"
                f"Thank you for registering!\n\n"
                f"Please verify your email by clicking the link below:\n\n"
                f"{verification_url}\n\n"
                f"This link will expire in 60 minutes.\n\n"
                f"Welcome to the platform!\n"
                f"Crowdfunding Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {
                "success": True,
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- LOGIN ----------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Login",
        description="Authenticate user and return JWT tokens. Indicates if email verification is needed.",
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginSuccessResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "tokens": inline_serializer(
                        "Tokens",
                        fields={
                            "refresh": serializers.CharField(),
                            "access": serializers.CharField(),
                        },
                    ),
                    "user": UserSerializer(),
                    "next_action": serializers.ChoiceField(choices=["VERIFY_EMAIL", "DASHBOARD"]),
                },
            )
        },
        examples=[
            OpenApiExample(
                "Successful Login (Verified User)",
                value={
                    "success": True,
                    "tokens": {
                        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
                    },
                    "user": {
                        "email": "investor@example.com",
                        "role": "INVESTOR",
                        "is_verified": True,
                    },
                    "next_action": "DASHBOARD",
                },
                response_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"success": False, "message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"success": False, "message": "Account is disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserSerializer(user).data,
                "next_action": "VERIFY_EMAIL" if not user.is_verified else "DASHBOARD",
            },
            status=status.HTTP_200_OK,
        )


# ---------------- LOGOUT ----------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout User (All Devices)",
        description="Blacklists all refresh tokens for the authenticated user.",
        responses={
            200: inline_serializer(
                name="LogoutResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request):
        try:
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
            return Response(
                {"success": True, "message": "Logged out successfully from all devices"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"success": False, "message": "Logout failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------- VERIFY EMAIL ----------------
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify User Email",
        description="Verifies email using token from verification email.",
        parameters=[
            OpenApiParameter(name="email", type=str, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="token", type=str, location=OpenApiParameter.QUERY, required=True),
        ],
        responses={
            200: inline_serializer(
                "VerifyResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def get(self, request):
        token = request.query_params.get("token")
        email = request.query_params.get("email")

        if not token or not email:
            return Response(
                {"success": False, "message": "Email and token are required"},
                status=400,
            )

        try:
            user = CustomUser.objects.get(email__iexact=email, verification_token=token)

            if user.verification_token_expiry < timezone.now():
                return Response(
                    {"success": False, "message": "Verification link has expired"},
                    status=400,
                )

            user.is_verified = True
            user.verification_token = None
            user.verification_token_expiry = None
            user.save(update_fields=["is_verified", "verification_token", "verification_token_expiry"])

            return Response(
                {"success": True, "message": "Email verified successfully! You can now invest."}
            )

        except CustomUser.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid or expired verification link"},
                status=400,
            )


# ---------------- RESEND VERIFICATION ----------------
class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend Verification Email",
        request=inline_serializer("ResendRequest", fields={"email": serializers.EmailField()}),
        responses={
            200: inline_serializer(
                "ResendResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"success": False, "message": "Email is required"}, status=400)

        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.is_verified:
                return Response({"success": False, "message": "Email is already verified"}, status=400)

            user.generate_verification_token()
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.verification_token}&email={user.email}"

            send_mail(
                subject="Verify Your Email - Crowdfunding Platform",
                message=(
                    f"Hi {user.email},\n\n"
                    f"We noticed you haven't verified your email yet.\n\n"
                    f"Click the link below to verify:\n\n"
                    f"{verification_url}\n\n"
                    f"Expires in 60 minutes.\n\n"
                    f"Thank you!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return Response({"success": True, "message": "Verification email sent again"})

        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)


# ---------------- PASSWORD RESET ----------------
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request Password Reset",
        description="Sends password reset link if user exists (safe - no email enumeration).",
        request=PasswordResetSerializer,
        responses={
            200: inline_serializer(
                "PasswordResetResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = CustomUser.objects.get(email__iexact=email)
            user.generate_password_reset_token()
            reset_url = f"{settings.FRONTEND_URL}/reset-password-confirm?token={user.password_reset_token}&email={user.email}"

            send_mail(
                subject="Password Reset Request",
                message=(
                    f"Hi {user.email},\n\n"
                    f"You requested a password reset.\n\n"
                    f"Click this link to set a new password:\n\n"
                    f"{reset_url}\n\n"
                    f"This link expires in 60 minutes.\n\n"
                    f"If you didn't request this, please ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except CustomUser.DoesNotExist:
            pass  # Never reveal if email exists

        return Response(
            {"success": True, "message": "If an account exists, a password reset link has been sent."}
        )


# ---------------- PASSWORD RESET CONFIRM ----------------
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Confirm Password Reset",
        description="Sets new password using token from reset email.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: inline_serializer(
                "PasswordResetConfirmResponse",
                fields={
                    "success": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = CustomUser.objects.get(email=email, password_reset_token=token)

            if user.password_reset_token_expiry < timezone.now():
                return Response({"success": False, "message": "Reset link has expired"}, status=400)

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_expiry = None
            user.save(update_fields=["password", "password_reset_token", "password_reset_token_expiry"])

            return Response(
                {"success": True, "message": "Password reset successful. You can now log in with your new password."}
            )

        except CustomUser.DoesNotExist:
            return Response({"success": False, "message": "Invalid or expired reset link"}, status=400)