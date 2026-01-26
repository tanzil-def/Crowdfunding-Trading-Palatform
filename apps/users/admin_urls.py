from django.urls import path
from .views import (
    AdminUserViewSet,
    AdminUserDetailView,
    AdminUserVerifyEmailView,
    AdminUserDeactivateView
)

urlpatterns = [
    path('', AdminUserViewSet.as_view(), name='user-list'),
    path('<uuid:id>/', AdminUserDetailView.as_view(), name='user-detail'),
    path('<uuid:id>/verify-email/', AdminUserVerifyEmailView.as_view(), name='user-verify'),
    path('<uuid:id>/deactivate/', AdminUserDeactivateView.as_view(), name='user-deactivate'),
]
