from django.urls import path
from .views import (
<<<<<<< HEAD
    RegisterView,
    LoginView,
    VerifyEmailView,
    ResendVerificationEmailView,
=======
    RegisterView, LoginView, LogoutView,
    VerifyEmailView, PasswordResetRequestView,
    PasswordResetConfirmView
>>>>>>> 83d38a9 (WIP: work in progress on project features)
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
<<<<<<< HEAD
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
]
=======
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
>>>>>>> 83d38a9 (WIP: work in progress on project features)
