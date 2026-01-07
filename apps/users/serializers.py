from rest_framework import serializers
<<<<<<< HEAD
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'role', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': True},
        }

    def validate_role(self, value):
        if value == CustomUser.Role.ADMIN:
            raise serializers.ValidationError("Cannot register as Admin. Use admin panel for admins.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data
=======
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=[('DEVELOPER','Developer'),('INVESTOR','Investor')], default='INVESTOR')
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('name','email','password','role')
>>>>>>> 83d38a9 (WIP: work in progress on project features)

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            role=validated_data.get('role','INVESTOR')
        )
<<<<<<< HEAD
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'role', 'is_verified']
=======

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
>>>>>>> 83d38a9 (WIP: work in progress on project features)
