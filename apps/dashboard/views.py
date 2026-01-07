from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.dashboard.services import get_developer_dashboard, get_investor_dashboard, get_admin_dashboard
from apps.users.permissions import IsDeveloper, IsInvestor, IsAdmin

# GET /dashboard/developer/
class DeveloperDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsDeveloper]

    def get(self, request):
        data = get_developer_dashboard(request.user)
        return Response({"success": True, "data": data})


# GET /dashboard/investor/
class InvestorDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsInvestor]

    def get(self, request):
        data = get_investor_dashboard(request.user)
        return Response({"success": True, "data": data})


# GET /dashboard/admin/
class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        data = get_admin_dashboard()
        return Response({"success": True, "data": data})
