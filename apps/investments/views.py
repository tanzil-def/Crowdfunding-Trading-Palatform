# apps/investments/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .serializers import (
    InitiateInvestmentSerializer,
    PaymentCallbackSerializer,
    SharePurchaseListSerializer
)
from .services import initiate_investment, confirm_payment
from .models import SharePurchase
from apps.users.permissions import IsInvestor
from apps.projects.models import Project


# POST /investments/initiate/
class InvestmentInitiateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = InitiateInvestmentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        shares_requested = serializer.validated_data['shares_requested']
        idempotency_key = serializer.validated_data['idempotency_key']

        project = get_object_or_404(Project, id=project_id, status='APPROVED')

        payment_info = initiate_investment(
            project=project,
            investor=request.user,
            shares_requested=shares_requested,
            idempotency_key=idempotency_key
        )

        return Response({
            "success": True,
            "message": "Investment initiated, proceed to payment gateway",
            "data": payment_info
        })


# POST /payments/callback/
class PaymentCallbackView(generics.GenericAPIView):
    serializer_class = PaymentCallbackSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirm_payment(
            payment_reference_id=serializer.validated_data['payment_reference_id'],
            gateway_payload=serializer.validated_data['gateway_payload'],
            admin_user=request.user,  # assuming admin triggers callback
            success=serializer.validated_data['success']
        )

        return Response({
            "success": True,
            "message": "Payment processed successfully"
        })


# GET /investments/my/
class MyInvestmentsListView(generics.ListAPIView):
    serializer_class = SharePurchaseListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        return SharePurchase.objects.filter(investor=self.request.user).order_by('-created_at')
