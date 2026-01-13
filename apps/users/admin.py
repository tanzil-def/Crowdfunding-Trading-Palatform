from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Wallet, WalletTransaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_verified', 
                   'is_active', 'is_banned', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_banned', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar', 'phone')}),
        ('Role & Status', {'fields': ('role', 'is_verified', 'is_active', 'is_banned')}),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Tokens', {
            'fields': ('verification_token', 'reset_token', 'reset_token_expiry'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 
                                      'created_at', 'updated_at', 'banned_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    actions = ['verify_users', 'ban_users', 'unban_users']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified.')
    verify_users.short_description = "Verify selected users"
    
    def ban_users(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_banned=True, banned_at=timezone.now())
        self.message_user(request, f'{updated} users banned.')
    ban_users.short_description = "Ban selected users"
    
    def unban_users(self, request, queryset):
        updated = queryset.update(is_banned=False, banned_at=None)
        self.message_user(request, f'{updated} users unbanned.')
    unban_users.short_description = "Unban selected users"


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'balance_formatted', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    
    def balance_formatted(self, obj):
        return f"${obj.balance:,.2f}"
    balance_formatted.short_description = 'Balance'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount_formatted', 'user_email', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('wallet__user__email', 'description')
    readonly_fields = ('created_at',)
    
    def amount_formatted(self, obj):
        return f"${obj.amount:,.2f}"
    amount_formatted.short_description = 'Amount'
    
    def user_email(self, obj):
        return obj.wallet.user.email
    user_email.admin_order_field = 'wallet__user__email'