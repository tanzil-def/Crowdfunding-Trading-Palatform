from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .serializers import InitiateInvestmentSerializer, PaymentCallbackSerializer, SharePurchaseListSerializer
from .services import initiate_investment, confirm_payment
from .models import SharePurchase
from apps.users.permissions import IsInvestor

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

        from apps.projects.models import Project
        project = get_object_or_404(Project, id=project_id, status='APPROVED')

        payment_info = initiate_investment(project, request.user, shares_requested, idempotency_key)
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
            serializer.validated_data['payment_reference_id'],
            serializer.validated_data['gateway_payload'],
            success=serializer.validated_data['success']
        )
        return Response({"success": True, "message": "Payment processed"})


# GET /investments/my/
class MyInvestmentsListView(generics.ListAPIView):
    serializer_class = SharePurchaseListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        return SharePurchase.objects.filter(investor=self.request.user)
