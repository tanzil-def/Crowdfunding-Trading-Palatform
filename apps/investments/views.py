from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Investment, PaymentTransaction
from .serializers import (
    InvestmentSerializer,
    InvestmentCreateSerializer,
    InvestmentReviewSerializer,
    PaymentTransactionSerializer,
    PaymentInitiateSerializer
)
from .services import InvestmentService, InvestmentAnalyticsService
from .permissions import (
    IsInvestorOwner,
    IsAdminUser,
    IsVerifiedInvestor,
    CanReviewInvestment
)
from utils.pagination import StandardResultsSetPagination
from utils.filters import InvestmentFilter


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for investment management[citation:1][citation:10]
    SRS: Complete investment workflow with proper access control
    """
    
    queryset = Investment.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvestmentFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'total_amount', 'shares']
    ordering = ['-created_at']
    search_fields = ['project__title', 'investor__email']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action[citation:9]"""
        if self.action == 'create':
            return InvestmentCreateSerializer
        elif self.action in ['review', 'admin_review']:
            return InvestmentReviewSerializer
        return InvestmentSerializer
    
    def get_permissions(self):
        """Apply permissions based on action[citation:7]"""
        if self.action in ['create', 'my_investments']:
            permission_classes = [permissions.IsAuthenticated, IsVerifiedInvestor]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInvestorOwner]
        elif self.action in ['review', 'admin_review', 'list_all']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['cancel', 'initiate_payment']:
            permission_classes = [permissions.IsAuthenticated, IsInvestorOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role[citation:7]"""
        user = self.request.user
        
        if user.is_admin:
            return super().get_queryset().select_related(
                'investor', 'project', 'reviewed_by'
            ).prefetch_related('payments')
        
        elif user.is_investor:
            return Investment.objects.filter(
                investor=user
            ).select_related('project').prefetch_related('payments')
        
        elif user.is_developer:
            return Investment.objects.filter(
                project__developer=user
            ).select_related('investor', 'project')
        
        return Investment.objects.none()
    
    def perform_create(self, serializer):
        """Create investment with service layer[citation:4]"""
        try:
            investment = InvestmentService.create_investment(
                investor=self.request.user,
                project=serializer.validated_data['project'],
                shares=serializer.validated_data['shares'],
                investor_notes=serializer.validated_data.get('investor_notes', '')
            )
            serializer.instance = investment
        except ValidationError as e:
            raise ValidationError(e.detail)
    
    @action(detail=False, methods=['get'])
    def my_investments(self, request):
        """Get current user's investments"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(investor=request.user)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def portfolio(self, request):
        """Get investor portfolio summary"""
        portfolio = InvestmentAnalyticsService.get_investor_portfolio(request.user)
        return Response(portfolio)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel investment request"""
        investment = self.get_object()
        
        try:
            investment = InvestmentService.cancel_investment(
                investment=investment,
                actor=request.user
            )
            serializer = self.get_serializer(investment)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        """Initiate payment for approved investment"""
        investment = self.get_object()
        serializer = PaymentInitiateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = InvestmentService.process_payment(
                investment=investment,
                payment_method=serializer.validated_data['payment_method'],
                reference_id=serializer.validated_data['reference_id'],
                request=request
            )
            
            payment_serializer = PaymentTransactionSerializer(payment)
            investment_serializer = self.get_serializer(investment)
            
            return Response({
                'investment': investment_serializer.data,
                'payment': payment_serializer.data,
                'message': 'Payment processed successfully'
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Admin review of investment (approve/reject)"""
        investment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            investment = InvestmentService.review_investment(
                investment=investment,
                reviewer=request.user,
                action=serializer.validated_data['action'],
                admin_notes=serializer.validated_data.get('admin_notes', ''),
                expires_in_days=serializer.validated_data.get('expires_in_days', 7)
            )
            
            return Response(self.get_serializer(investment).data)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get investment statistics (admin only)"""
        if not request.user.is_admin:
            raise PermissionDenied('Admin access required')
        
        total_investments = Investment.objects.count()
        completed_investments = Investment.objects.filter(
            status=Investment.Status.COMPLETED
        ).count()
        total_funding = sum(
            inv.total_amount 
            for inv in Investment.objects.filter(
                status=Investment.Status.COMPLETED
            )
        )
        
        return Response({
            'total_investments': total_investments,
            'completed_investments': completed_investments,
            'total_funding': float(total_funding),
            'pending_review': Investment.objects.filter(
                status=Investment.Status.REQUESTED
            ).count()
        })


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payment transaction viewing[citation:7]
    SRS: Payment and investment logs for audit
    """
    
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter payments based on user role"""
        user = self.request.user
        
        if user.is_admin:
            return PaymentTransaction.objects.all().select_related(
                'investment', 'investment__project', 'investment__investor'
            )
        
        elif user.is_investor:
            return PaymentTransaction.objects.filter(
                investment__investor=user
            ).select_related('investment', 'investment__project')
        
        elif user.is_developer:
            return PaymentTransaction.objects.filter(
                investment__project__developer=user
            ).select_related('investment', 'investment__investor')
        
        return PaymentTransaction.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Get current user's payments"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(investment__investor=request.user)
        )
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)