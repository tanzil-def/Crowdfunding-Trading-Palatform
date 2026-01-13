from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from .models import User, Wallet, WalletTransaction


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile (read operations)"""
    
    full_name = serializers.SerializerMethodField()
    wallet_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'role', 'is_verified', 'is_active', 'date_joined',
            'avatar', 'phone', 'wallet_balance'
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified']
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_wallet_balance(self, obj):
        try:
            return obj.wallet.balance
        except Wallet.DoesNotExist:
            return 0.00


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration (SRS: Email verification required)"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        # Check password confirmation
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Role validation (SRS: Only Developer or Investor can register)
        role = attrs.get('role')
        if role == User.Role.ADMIN:
            raise serializers.ValidationError({
                'role': 'Cannot register as admin.'
            })
        
        return attrs
    
    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', User.Role.INVESTOR)
        )
        
        # Create wallet for user
        Wallet.objects.create(user=user)
        
        # Send verification email (SRS requirement)
        user.send_verification_email()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar', 'phone']
    
    def validate_phone(self, value):
        # Basic phone validation
        if value and not value.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise serializers.ValidationError('Enter a valid phone number.')
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Additional validation can be added here
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    
    token = serializers.UUIDField(required=True)
    
    def validate_token(self, value):
        try:
            user = User.objects.get(verification_token=value)
            
            # Check if token is expired (24 hours)
            if user.verification_sent_at and \
               (timezone.now() - user.verification_sent_at).total_seconds() > 86400:
                raise serializers.ValidationError('Verification token has expired.')
            
            # Check if already verified
            if user.is_verified:
                raise serializers.ValidationError('Email is already verified.')
            
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid verification token.')


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError('No user found with this email.')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.UUIDField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate token
        try:
            user = User.objects.get(reset_token=attrs['token'])
            
            if user.reset_token_expiry and user.reset_token_expiry < timezone.now():
                raise serializers.ValidationError({
                    'token': 'Reset token has expired.'
                })
            
            attrs['user'] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'token': 'Invalid reset token.'
            })


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for user wallet"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user_email', 'balance', 'created_at', 'updated_at']
        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions"""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'amount', 'type', 'description',
            'reference_id', 'reference_type',
            'metadata', 'created_at'
        ]
        read_only_fields = fields