from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, APIException

from .serializers import (
    InitiateInvestmentSerializer,
    InvestmentInitiateResponseSerializer,
    PaymentCallbackSerializer,
    SharePurchaseListSerializer,
    SharePurchaseDetailSerializer,
    PaymentTransactionSerializer,
    PortfolioSummarySerializer
)
from .services import initiate_investment, confirm_payment, get_investor_portfolio_summary
from .models import SharePurchase, PaymentTransaction
from apps.projects.models import Project

# Import permissions
try:
    from utils.permissions import IsInvestor, IsAdmin
except ImportError:
    from apps.favorites.permissions import IsInvestor
    from utils.permissions import IsAdmin

from utils.responses import success_response, error_response


class InvestmentInitiateView(generics.GenericAPIView):
    """
    POST /api/v1/investments/initiate/
    
    Initiate investment process for an approved project.
    
    SRS Requirements:
    - Email verification required (403 if unverified)
    - Only approved projects (400 if not approved)
    - Share availability check (400 if insufficient)
    - Idempotency support (409 if duplicate)
    
    Request Body:
        - project_id (UUID): Project to invest in
        - shares_requested (int): Number of shares to purchase
        - idempotency_key (string): Unique transaction reference
    
    Response:
        - project_id (UUID): Project identifier
        - shares_requested (int): Number of shares requested
        - idempotency_key (string): Transaction reference
        - reference_id (UUID): Payment transaction ID
        - payment_url (string): URL to redirect for payment
    """
    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = InitiateInvestmentSerializer

    @extend_schema(
        responses=InvestmentInitiateResponseSerializer,
        description="Initiate investment process for an approved project. \n\n"
                    "Backend uses atomic database transaction with row-level locking "
                    "(select_for_update) to prevent overselling under concurrent requests."
    )
    def post(self, request):
        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        shares_requested = serializer.validated_data['shares_requested']
        idempotency_key = serializer.validated_data['idempotency_key']

        # Get project or return 404
        project = get_object_or_404(Project, id=project_id)

        try:
            # Call service layer for business logic
            payment_info = initiate_investment(
                project=project,
                investor=request.user,
                shares_requested=shares_requested,
                idempotency_key=idempotency_key
            )

            # Serialize response
            response_serializer = InvestmentInitiateResponseSerializer(payment_info)

            return success_response(
                data=response_serializer.data,
                message="Investment initiated successfully. Proceed to payment gateway.",
                status_code=status.HTTP_201_CREATED
            )

        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            if isinstance(detail, dict):
                message = detail.get('detail', "Validation error")
                errors = detail
            else:
                message = str(detail)
                errors = None
                
            return error_response(
                message=message,
                errors=errors,
                status_code=status_code
            )


class PaymentCallbackView(generics.GenericAPIView):
    """
    POST /api/v1/investments/payments/callback/
    
    Payment gateway webhook endpoint.
    Processes payment confirmations and creates share purchases.
    
    SRS Requirements:
    - Idempotent processing (409 if already processed)
    - Prevents duplicate callbacks
    - Atomic share allocation with select_for_update
    - Audit logging
    
    Note: This endpoint allows unauthenticated requests from payment gateway.
    In production, implement proper signature verification.
    
    Request Body:
        - payment_reference_id (string): Transaction reference
        - success (boolean): Payment success status
        - gateway_payload (object): Raw gateway data
    """
    permission_classes = [AllowAny]
    serializer_class = PaymentCallbackSerializer

    @extend_schema(
        description="Payment gateway webhook endpoint. \n\n"
                    "This is a webhook endpoint. In production: MUST verify gateway signature "
                    "(e.g. X-Signature header) before processing. Currently documented as "
                    "unauthenticated for sandbox/testing only."
    )
    def post(self, request):
        # Validate callback data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_reference_id = serializer.validated_data['payment_reference_id']
        gateway_payload = serializer.validated_data['gateway_payload']
        success = serializer.validated_data['success']

        try:
            # Call service layer for payment confirmation
            result = confirm_payment(
                payment_reference_id=payment_reference_id,
                gateway_payload=gateway_payload,
                success=success
            )

            return success_response(
                data=result,
                message="Payment callback processed successfully",
                status_code=status.HTTP_200_OK
            )

        except (ValidationError, APIException) as e:
            status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            detail = getattr(e, 'detail', str(e))
            if isinstance(detail, dict):
                message = detail.get('detail', "Validation error")
                errors = detail
            else:
                message = str(detail)
                errors = None

            return error_response(
                message=message,
                errors=errors,
                status_code=status_code
            )


class MyInvestmentsListView(generics.ListAPIView):
    """
    GET /api/v1/investments/my/
    
    List all share purchases made by the authenticated investor.
    
    SRS Requirements:
    - Show investment history
    - Include project details
    - Ordered by most recent
    - Support search and ordering
    
    Query Parameters:
        - search: Search in project title or payment reference
        - ordering: Order by created_at, total_amount, or shares_purchased
        - page: Page number for pagination
        - page_size: Number of results per page
    """
    serializer_class = SharePurchaseListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['project__title', 'payment__reference_id']
    ordering_fields = ['created_at', 'total_amount', 'shares_purchased']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        """
        Return share purchases for authenticated investor.
        Optimized with select_related to prevent N+1 queries.
        """
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return SharePurchase.objects.none()
        
        return SharePurchase.objects.filter(
            investor=self.request.user
        ).select_related(
            'project',
            'payment'
        ).order_by('-created_at')


from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes


class InvestmentDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/investments/{id}/
    
    Retrieve detailed information about a specific investment.
    Used for receipts and transaction details.
    
    SRS Requirements:
    - Detailed investment information
    - Include project status and shares sold
    - Include payment transaction details
    """
    serializer_class = SharePurchaseDetailSerializer
    permission_classes = [IsAuthenticated, IsInvestor]
    lookup_field = 'id'

    @extend_schema(
        examples=[
            OpenApiExample(
                'Investment Detail Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                        "project_id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
                        "project_title": "Green Energy Park",
                        "project_status": "APPROVED",
                        "project_total_shares": 1000,
                        "project_shares_sold": 450,
                        "shares_purchased": 10,
                        "price_per_share": "1500.00",
                        "total_amount": "15000.00",
                        "payment_details": {
                            "reference_id": "TXN-12345",
                            "status": "SUCCESS",
                            "processed_at": "2026-01-20T10:00:00Z"
                        },
                        "created_at": "2026-01-20T10:00:00Z"
                    }
                },
                response_only=True,
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return share purchases for authenticated investor only.
        Ensures investors can only view their own investments.
        """
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return SharePurchase.objects.none()
        
        return SharePurchase.objects.filter(
            investor=self.request.user
        ).select_related('project', 'payment')


class InvestorPortfolioSummaryView(generics.GenericAPIView):
    """
    GET /api/v1/investments/portfolio/summary/
    
    Get investor's portfolio summary for dashboard.
    
    SRS Requirements:
    - Total invested amount
    - Number of projects invested
    - Total shares owned
    - Investment count
    
    Response uses optimized aggregation queries for performance.
    """
    serializer_class = PortfolioSummarySerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    @extend_schema(
        examples=[
            OpenApiExample(
                'Portfolio Summary Example',
                value={
                    "success": True,
                    "message": "Portfolio summary retrieved successfully",
                    "data": {
                        "total_invested": "250000.75",
                        "projects_invested": 12,
                        "total_shares_owned": 1500,
                        "investment_count": 24
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request):
        # Call service layer for portfolio summary
        summary = get_investor_portfolio_summary(request.user)
        
        # Serialize response
        serializer = self.get_serializer(summary)
        
        return success_response(
            data=serializer.data,
            message="Portfolio summary retrieved successfully"
        )


class AdminPaymentTransactionListView(generics.ListAPIView):
    """
    GET /api/v1/investments/admin/transactions/
    
    Admin view of all payment transactions for audit purposes.
    
    SRS Requirements:
    - Admin can review all transactions
    - Includes success and failures
    - Audit trail support
    - Support search, filtering, and ordering
    
    Query Parameters:
        - search: Search in reference_id, investor email, or project title
        - ordering: Order by created_at, amount, or status
        - status: Filter by transaction status (INITIATED, SUCCESS, FAILED)
        - page: Page number for pagination
        - page_size: Number of results per page
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        examples=[
            OpenApiExample(
                'Admin Transactions Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": "92f7d9e6-f29a-46e0-9899-f0dd317403a7",
                                "reference_id": "TXN-887766",
                                "investor_email": "i***r@example.com",
                                "project_title": "Green Energy Park",
                                "amount": "5000.00",
                                "status": "SUCCESS",
                                "has_share_purchase": True,
                                "failure_reason": None,
                                "created_at": "2026-01-20T11:00:00Z",
                                "processed_at": "2026-01-20T11:05:00Z"
                            }
                        ]
                    }
                },
                response_only=True,
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['reference_id', 'investor__email', 'project__title']
    ordering_fields = ['created_at', 'amount', 'status']
    filterset_fields = ['status']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        """
        Return all payment transactions with related data.
        Optimized with select_related to prevent N+1 queries.
        """
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return PaymentTransaction.objects.none()
        
        return PaymentTransaction.objects.all().select_related(
            'investor',
            'project'
        ).order_by('-created_at')


class AdminPaymentTransactionDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/investments/admin/transactions/{id}/
    
    Admin view of individual payment transaction details.
    
    SRS Requirements:
    - Admin can view detailed transaction information
    - Includes all transaction metadata
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Return all payment transactions for admin users.
        """
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return PaymentTransaction.objects.none()
        
        return PaymentTransaction.objects.all().select_related(
            'investor',
            'project'
        )