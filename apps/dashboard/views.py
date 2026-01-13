# apps/dashboard/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.dashboard.services import (
    get_developer_dashboard,
    get_investor_dashboard,
    get_admin_dashboard
)
from apps.users.permissions import IsDeveloperUser, IsInvestorUser, IsAdminUser


class BaseDashboardView(generics.GenericAPIView):
    """
    Base class for dashboard views.
    Handles standard GET response structure.
    """

    def get_success_response(self, data):
        return Response({"success": True, "data": data})


class DeveloperDashboardView(BaseDashboardView):
    """
    Developer dashboard endpoint
    GET /dashboard/developer/
    """
    permission_classes = [IsAuthenticated, IsDeveloperUser]

    def get(self, request, *args, **kwargs):
        data = get_developer_dashboard(request.user)
        return self.get_success_response(data)


class InvestorDashboardView(BaseDashboardView):
    """
    Investor dashboard endpoint
    GET /dashboard/investor/
    """
    permission_classes = [IsAuthenticated, IsInvestorUser]

    def get(self, request, *args, **kwargs):
        data = get_investor_dashboard(request.user)
        return self.get_success_response(data)


class AdminDashboardView(BaseDashboardView):
    """
    Admin dashboard endpoint
    GET /dashboard/admin/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, *args, **kwargs):
        data = get_admin_dashboard()
        return self.get_success_response(data)
