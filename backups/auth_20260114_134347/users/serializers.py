from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer.
    
    SRS Requirements:
    - Email and password required
    - First name and last name required
    - Role selection (Developer or Investor only)
    - Password validation
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters with letters and numbers"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Must match password field"
    )
    role = serializers.ChoiceField(
        choices=[
            (User.ROLE_DEVELOPER, 'Developer'),
            (User.ROLE_INVESTOR, 'Investor')
        ],
        required=True,
        help_text="Select your role: Developer or Investor"
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'role'
        ]
    
    def validate_role(self, value):
        """Only allow Developer and Investor roles"""
        if value not in [User.ROLE_DEVELOPER, User.ROLE_INVESTOR]:
            raise serializers.ValidationError(
                "Only Developer and Investor roles are allowed for registration."
            )
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        """Validate password match and strength"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    User login serializer.
    SRS: Login with email and password.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class GoogleOAuthSerializer(serializers.Serializer):
    """
    Google OAuth serializer.
    SRS: Support OAuth authentication.
    """
    token = serializers.CharField(required=True)
    role = serializers.ChoiceField(
        choices=[User.ROLE_DEVELOPER, User.ROLE_INVESTOR],
        required=False,
        default=User.ROLE_INVESTOR
    )


class EmailVerificationSerializer(serializers.Serializer):
    """
    Email verification serializer.
    SRS: Email verification required.
    """
    token = serializers.CharField(required=True, max_length=64)


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password reset request serializer.
    SRS: Users can reset password via email.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password reset confirmation serializer.
    """
    token = serializers.CharField(required=True, max_length=64)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate password match and strength"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for viewing user information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'auth_provider',
            'is_email_verified',
            'date_joined'
        ]
        read_only_fields = fields


class TokenResponseSerializer(serializers.Serializer):
    """
    JWT token response serializer.
    SRS: Clean token response format.
    """
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)