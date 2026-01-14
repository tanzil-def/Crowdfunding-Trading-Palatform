from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = [
        'email',
        'role',
        'auth_method',
        'is_email_verified',
        'is_active',
        'date_joined'
    ]
    list_filter = [
        'role',
        'auth_method',
        'is_email_verified',
        'is_active',
        'is_staff',
        'date_joined'
    ]
    search_fields = [
        'email',
        'first_name',
        'last_name'
    ]
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'profile_picture')
        }),
        ('Role & Authentication', {
            'fields': ('role', 'auth_method', 'google_id')
        }),
        ('Permissions', {
            'fields': (
                'is_email_verified',
                'is_active',
                'is_staff',
                'is_superuser'
            )
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'role',
                'password1',
                'password2',
                'is_email_verified',
                'is_active'
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for email verification tokens.
    """
    list_display = [
        'user',
        'token',
        'created_at',
        'expires_at',
        'is_used'
    ]
    list_filter = [
        'is_used',
        'created_at',
        'expires_at'
    ]
    search_fields = [
        'user__email',
        'token'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'created_at',
        'expires_at'
    ]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for password reset tokens.
    """
    list_display = [
        'user',
        'token',
        'created_at',
        'expires_at',
        'is_used'
    ]
    list_filter = [
        'is_used',
        'created_at',
        'expires_at'
    ]
    search_fields = [
        'user__email',
        'token'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'created_at',
        'expires_at'
    ]