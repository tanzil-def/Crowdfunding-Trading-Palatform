from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(
        choices=[('DEVELOPER', 'Developer'), ('INVESTOR', 'Investor')],
        default='INVESTOR'
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'password', 'role')

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            role=validated_data.get('role', 'INVESTOR')
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'role', 'is_email_verified')


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)
