from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    VerifyEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    LogoutView,  
)

app_name = "users"

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),  # <-- New route
]
