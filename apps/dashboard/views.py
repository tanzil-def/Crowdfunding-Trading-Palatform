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

# GET /dashboard/developer/
class DeveloperDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsDeveloper]
    serializer_class = DeveloperDashboardSerializer

    def get(self, request):
        data = get_developer_dashboard(request.user)
        serializer = self.get_serializer(data)
        return Response({"success": True, "data": serializer.data})


# GET /dashboard/investor/
class InvestorDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = InvestorDashboardSerializer

    def get(self, request):
        data = get_investor_dashboard(request.user)
        serializer = self.get_serializer(data)
        return Response({"success": True, "data": serializer.data})


# GET /dashboard/admin/
class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminDashboardSerializer

    def get(self, request):
        data = get_admin_dashboard()
        serializer = self.get_serializer(data)
        return Response({"success": True, "data": serializer.data})
