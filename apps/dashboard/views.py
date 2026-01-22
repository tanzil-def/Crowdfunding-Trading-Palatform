from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.dashboard.services import get_developer_dashboard, get_investor_dashboard, get_admin_dashboard
from apps.dashboard.serializers import (
    DeveloperDashboardSerializer, 
    InvestorDashboardSerializer, 
    AdminDashboardSerializer
)
from apps.users.permissions import IsDeveloper, IsInvestor, IsAdmin
from drf_spectacular.utils import extend_schema, OpenApiExample
from utils.responses import success_response


# GET /dashboard/developer/
class DeveloperDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsDeveloper]
    serializer_class = DeveloperDashboardSerializer

    @extend_schema(
        examples=[
            OpenApiExample(
                'Developer Dashboard Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "total_projects": 5,
                        "total_shares_sold": 1200,
                        "total_investment_received": "450000.00",
                        "pending_projects": 2,
                        "unread_notifications": 3
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request):
        data = get_developer_dashboard(request.user)
        serializer = self.get_serializer(data)
        return success_response(data=serializer.data)


# GET /dashboard/investor/
class InvestorDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = InvestorDashboardSerializer

    @extend_schema(
        examples=[
            OpenApiExample(
                'Investor Dashboard Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "total_investments": 12,
                        "portfolio_value": "320000.50",
                        "favorite_projects": 8,
                        "unread_notifications": 1
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request):
        data = get_investor_dashboard(request.user)
        serializer = self.get_serializer(data)
        return success_response(data=serializer.data)


# GET /dashboard/admin/
class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminDashboardSerializer

    @extend_schema(
        examples=[
            OpenApiExample(
                'Admin Dashboard Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "total_projects": 45,
                        "pending_projects": 7,
                        "total_investments": 156,
                        "total_revenue": "150000.00",
                        "unread_notifications": 12
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request):
        data = get_admin_dashboard()
        serializer = self.get_serializer(data)
        return success_response(data=serializer.data)
