from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    
    list_display = [
        'email',
        'first_name',
        'last_name',
        'role',
        'is_email_verified',
        'auth_provider',
        'is_active',
        'date_joined'
    ]
    list_filter = [
        'role',
        'is_email_verified',
        'auth_provider',
        'is_active',
        'is_staff',
        'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Account Info', {
            'fields': ('role', 'auth_provider', 'google_id')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_email_verified',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'role',
                'is_email_verified',
                'is_active',
                'is_staff'
            )
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin interface for Email Verification Tokens"""
    
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']
    ordering = ['-created_at']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for Password Reset Tokens"""
    
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']
    ordering = ['-created_at']