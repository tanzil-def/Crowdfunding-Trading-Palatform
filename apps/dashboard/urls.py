from django.urls import path
from .views import DeveloperDashboardView, InvestorDashboardView, AdminDashboardView

urlpatterns = [
    path('developer/', DeveloperDashboardView.as_view(), name='dashboard-developer'),
    path('investor/', InvestorDashboardView.as_view(), name='dashboard-investor'),
    path('admin/', AdminDashboardView.as_view(), name='dashboard-admin'),
]
