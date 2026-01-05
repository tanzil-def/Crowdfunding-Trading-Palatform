from rest_framework import serializers
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'role', 'password', 'password2']

    def validate_role(self, value):
        if value == CustomUser.Role.ADMIN:
            raise serializers.ValidationError("Cannot register as Admin. Use Django admin panel.")
        if value not in [CustomUser.Role.INVESTOR, CustomUser.Role.DEVELOPER]:
            raise serializers.ValidationError("Role must be either INVESTOR or DEVELOPER.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": ["Passwords must match."]})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        user.generate_verification_token()  # from models.py method
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="User email address")
    password = serializers.CharField(style={'input_type': 'password'}, help_text="User password")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'role', 'is_verified']
        read_only_fields = ['email', 'role', 'is_verified']


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email of the account to reset password")


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})