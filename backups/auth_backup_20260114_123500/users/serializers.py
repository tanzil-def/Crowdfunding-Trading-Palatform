from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings


class UserRegistrationSerializer(serializers.Serializer):
    """
    User registration serializer.
    SRS Requirement: Email-based registration with role selection.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150
    )
    
    def validate_email(self, value):
        """Check if email is already registered."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value.lower()
    
    def validate(self, data):
        """Validate password matching and strength."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        validate_password(data['password'])
        
        return data
    
    def create(self, validated_data):
        """Create new user account."""
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            auth_method=User.AUTH_METHOD_EMAIL
        )
        
        return user


class GoogleOAuthSerializer(serializers.Serializer):
    """
    Google OAuth login serializer.
    Verifies Google ID token and creates/updates user.
    """
    credential = serializers.CharField(required=True)
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        help_text="Required for first-time Google sign-up"
    )
    
    def validate_credential(self, value):
        """Verify Google ID token and extract user info."""
        try:
            google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
            
            if not google_client_id:
                raise serializers.ValidationError(
                    "Google OAuth not configured on server."
                )
            
            idinfo = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                google_client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError("Invalid token issuer.")
            
            return idinfo
            
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid Google token: {str(e)}")
    
    def create(self, validated_data):
        """Create or update user from Google OAuth."""
        idinfo = validated_data['credential']
        role = validated_data['role']
        
        email = idinfo['email']
        google_id = idinfo['sub']
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        picture = idinfo.get('picture', '')
        
        try:
            user = User.objects.get(email=email)
            
            if not user.google_id:
                user.google_id = google_id
                user.auth_method = User.AUTH_METHOD_GOOGLE
                user.is_email_verified = True
            
            if picture and not user.profile_picture:
                user.profile_picture = picture
            
            user.save()
            
        except User.DoesNotExist:
            user = User.objects.create_google_user(
                email=email,
                google_id=google_id,
                role=role,
                first_name=first_name,
                last_name=last_name,
                profile_picture=picture
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Email/password login serializer.
    SRS Requirement: Secure login functionality.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Authenticate user credentials."""
        email = data.get('email', '').lower()
        password = data.get('password')
        
        user = authenticate(email=email, password=password)
        
        if not user:
            raise serializers.ValidationError(
                "Invalid email or password."
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "This account has been deactivated."
            )
        
        data['user'] = user
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """
    Email verification serializer.
    SRS Requirement: Email verification required before investing.
    """
    token = serializers.CharField(required=True)


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Resend verification email to user."""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists and needs verification."""
        try:
            user = User.objects.get(email=value.lower())
            
            if user.is_email_verified:
                raise serializers.ValidationError(
                    "This email is already verified."
                )
            
            return user
            
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No account found with this email."
            )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password reset request serializer.
    SRS Requirement: Password reset via email.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists."""
        try:
            user = User.objects.get(email=value.lower())
            
            if user.auth_method == User.AUTH_METHOD_GOOGLE:
                raise serializers.ValidationError(
                    "This account uses Google sign-in. Password reset not available."
                )
            
            return user
            
        except User.DoesNotExist:
            return None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password reset confirmation serializer.
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Validate password matching and strength."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        validate_password(data['password'])
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for viewing and updating profile.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    can_invest = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'auth_method',
            'profile_picture',
            'is_email_verified',
            'can_invest',
            'date_joined',
            'last_login'
        ]
        read_only_fields = [
            'id',
            'email',
            'role',
            'auth_method',
            'is_email_verified',
            'date_joined',
            'last_login'
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'profile_picture'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Change password for authenticated users.
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Verify old password is correct."""
        user = self.context['request'].user
        
        if user.auth_method == User.AUTH_METHOD_GOOGLE:
            raise serializers.ValidationError(
                "Password change not available for Google accounts."
            )
        
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )
        
        return value
    
    def validate(self, data):
        """Validate new password matching and strength."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Passwords do not match."
            })
        
        validate_password(data['new_password'])
        
        return data