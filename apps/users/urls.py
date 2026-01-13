from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfileView,
    WalletView,
    WalletTransactionView,
    UserListView,
    UserDetailView,
    BanUserView,
    ResendVerificationView,
    CustomTokenRefreshView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User profile
    path('me/', UserProfileView.as_view(), name='me'),
    
    # Wallet
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('wallet/transactions/', WalletTransactionView.as_view(), name='wallet-transactions'),
    
    # Admin endpoints
    path('admin/users/', UserListView.as_view(), name='admin-user-list'),
    path('admin/users/<uuid:user_id>/', UserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<uuid:user_id>/ban/', BanUserView.as_view(), name='admin-user-ban'),
    path('admin/users/<uuid:user_id>/resend-verification/', 
         ResendVerificationView.as_view(), name='admin-resend-verification'),
]