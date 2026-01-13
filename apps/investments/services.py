import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import Investment, PaymentTransaction, InvestmentAuditLog
from apps.projects.models import Project
from apps.users.models import User
from apps.notifications.services import send_notification

logger = logging.getLogger(__name__)


class InvestmentService:
    """Service layer for investment business logic[citation:4]"""
    
    @staticmethod
    @transaction.atomic
    def create_investment(
        investor: User,
        project: Project,
        shares: int,
        investor_notes: str = ''
    ) -> Investment:
        """
        Create a new investment request with atomic validation[citation:1]
        SRS: Share allocation must be atomic to prevent overselling
        """
        # Lock project for update to prevent race conditions
        locked_project = Project.objects.select_for_update().get(id=project.id)
        
        # Validate share availability
        if shares > locked_project.remaining_shares:
            raise ValidationError({
                'shares': f'Only {locked_project.remaining_shares} shares available'
            })
        
        # Calculate investment details
        price_per_share = locked_project.per_share_price
        total_amount = Decimal(shares) * price_per_share
        
        # Create investment
        investment = Investment.objects.create(
            investor=investor,
            project=locked_project,
            shares=shares,
            price_per_share=price_per_share,
            total_amount=total_amount,
            investor_notes=investor_notes,
            created_by=investor
        )
        
        # Create audit log
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=investor,
            action_type=InvestmentAuditLog.ActionType.CREATED,
            description=f'Investment request for {shares} shares created',
            metadata={
                'shares': shares,
                'price_per_share': str(price_per_share),
                'total_amount': str(total_amount)
            }
        )
        
        # Send notification to admins
        send_notification(
            recipients='admins',
            notification_type='INVESTMENT_REQUESTED',
            title='New Investment Request',
            message=f'{investor.email} requested {shares} shares in {project.title}',
            related_object=investment
        )
        
        logger.info(
            f'Investment created: {investment.id}, '
            f'Investor: {investor.email}, '
            f'Shares: {shares}, '
            f'Project: {project.title}'
        )
        
        return investment
    
    @staticmethod
    @transaction.atomic
    def review_investment(
        investment: Investment,
        reviewer: User,
        action: str,
        admin_notes: str = '',
        expires_in_days: int = 7
    ) -> Investment:
        """
        Admin review of investment request[citation:7]
        SRS: Admin can approve, reject, or request changes
        """
        if investment.status != Investment.Status.REQUESTED:
            raise ValidationError('Investment is not in requested status')
        
        if action == 'approve':
            investment.status = Investment.Status.APPROVED
            investment.approval_expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
            action_type = InvestmentAuditLog.ActionType.APPROVED
            notification_type = 'INVESTMENT_APPROVED'
        elif action == 'reject':
            investment.status = Investment.Status.REJECTED
            action_type = InvestmentAuditLog.ActionType.REJECTED
            notification_type = 'INVESTMENT_REJECTED'
        else:
            raise ValidationError('Invalid review action')
        
        investment.reviewed_at = timezone.now()
        investment.reviewed_by = reviewer
        investment.admin_notes = admin_notes
        investment.save()
        
        # Create audit log
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=reviewer,
            action_type=action_type,
            description=f'Investment {action} by admin',
            previous_status=Investment.Status.REQUESTED,
            new_status=investment.status,
            metadata={
                'admin_notes': admin_notes,
                'expires_at': investment.approval_expires_at.isoformat() if investment.approval_expires_at else None
            }
        )
        
        # Send notification to investor
        send_notification(
            recipients=[investment.investor],
            notification_type=notification_type,
            title=f'Investment {action.capitalize()}',
            message=f'Your investment in {investment.project.title} has been {action}',
            related_object=investment
        )
        
        logger.info(
            f'Investment reviewed: {investment.id}, '
            f'Action: {action}, '
            f'Reviewer: {reviewer.email}'
        )
        
        return investment
    
    @staticmethod
    @transaction.atomic
    def process_payment(
        investment: Investment,
        payment_method: str,
        reference_id: str,
        request=None
    ) -> PaymentTransaction:
        """
        Process payment for approved investment[citation:1]
        SRS: Idempotent payment handling with duplicate prevention
        """
        if investment.status != Investment.Status.APPROVED:
            raise ValidationError('Investment is not approved for payment')
        
        if investment.approval_expires_at and investment.approval_expires_at < timezone.now():
            InvestmentService.expire_investment(investment)
            raise ValidationError('Investment approval has expired')
        
        # Check for existing successful payment
        existing_payment = investment.payments.filter(
            status=PaymentTransaction.Status.SUCCESS
        ).first()
        
        if existing_payment:
            raise ValidationError('Payment already processed for this investment')
        
        # Generate transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment transaction
        payment = PaymentTransaction.objects.create(
            transaction_id=transaction_id,
            reference_id=reference_id,
            investment=investment,
            amount=investment.total_amount,
            payment_method=payment_method,
            created_by=investment.investor,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else None
        )
        
        # Update investment status
        investment.status = Investment.Status.PROCESSING
        investment.save()
        
        # Create audit logs
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=investment.investor,
            action_type=InvestmentAuditLog.ActionType.PAYMENT_INITIATED,
            description='Payment initiated',
            previous_status=Investment.Status.APPROVED,
            new_status=Investment.Status.PROCESSING,
            metadata={
                'transaction_id': transaction_id,
                'payment_method': payment_method,
                'amount': str(investment.total_amount)
            }
        )
        
        # Process payment (sandbox implementation)
        try:
            # Simulate payment processing
            # In production, integrate with actual payment gateway
            payment.status = PaymentTransaction.Status.SUCCESS
            payment.gateway_transaction_id = f"GATEWAY-{uuid.uuid4().hex[:8]}"
            payment.processed_at = timezone.now()
            payment.gateway_response = {
                'status': 'success',
                'message': 'Payment processed successfully',
                'sandbox': True
            }
            payment.save()
            
            # Update investment
            InvestmentService.complete_investment(investment, payment)
            
            logger.info(
                f'Payment successful: {payment.transaction_id}, '
                f'Investment: {investment.id}, '
                f'Amount: {payment.amount}'
            )
            
        except Exception as e:
            # Handle payment failure
            payment.status = PaymentTransaction.Status.FAILED
            payment.gateway_response = {
                'status': 'failed',
                'error': str(e),
                'sandbox': True
            }
            payment.save()
            
            InvestmentAuditLog.objects.create(
                investment=investment,
                actor=investment.investor,
                action_type=InvestmentAuditLog.ActionType.PAYMENT_FAILED,
                description='Payment processing failed',
                metadata={'error': str(e)}
            )
            
            logger.error(
                f'Payment failed: {payment.transaction_id}, '
                f'Error: {str(e)}'
            )
            
            raise ValidationError(f'Payment processing failed: {str(e)}')
        
        return payment
    
    @staticmethod
    @transaction.atomic
    def complete_investment(investment: Investment, payment: PaymentTransaction) -> Investment:
        """
        Complete investment after successful payment[citation:1]
        SRS: Successful payments update shares and dashboards
        """
        # Lock project for atomic update
        project = Project.objects.select_for_update().get(id=investment.project.id)
        
        # Validate share availability
        if investment.shares > project.remaining_shares:
            raise ValidationError(
                f'Insufficient shares available. '
                f'Requested: {investment.shares}, '
                f'Available: {project.remaining_shares}'
            )
        
        # Update project shares
        project.shares_sold += investment.shares
        project.save()
        
        # Update investment status
        investment.status = Investment.Status.COMPLETED
        investment.completed_at = timezone.now()
        investment.save()
        
        # Create audit logs
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=investment.investor,
            action_type=InvestmentAuditLog.ActionType.COMPLETED,
            description='Investment completed successfully',
            previous_status=Investment.Status.PROCESSING,
            new_status=Investment.Status.COMPLETED,
            metadata={
                'shares_allocated': investment.shares,
                'project_shares_sold': project.shares_sold,
                'payment_id': str(payment.id)
            }
        )
        
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=investment.investor,
            action_type=InvestmentAuditLog.ActionType.PAYMENT_SUCCESS,
            description='Payment successful',
            metadata={
                'transaction_id': payment.transaction_id,
                'amount': str(payment.amount)
            }
        )
        
        # Send notifications
        send_notification(
            recipients=[investment.investor],
            notification_type='INVESTMENT_COMPLETED',
            title='Investment Completed',
            message=f'Your investment in {project.title} has been completed successfully',
            related_object=investment
        )
        
        send_notification(
            recipients=[project.developer],
            notification_type='PROJECT_FUNDING_UPDATED',
            title='New Investment Received',
            message=f'{investment.investor.email} invested in {project.title}',
            related_object=project
        )
        
        logger.info(
            f'Investment completed: {investment.id}, '
            f'Shares: {investment.shares}, '
            f'Project: {project.title}'
        )
        
        return investment
    
    @staticmethod
    def expire_investment(investment: Investment) -> None:
        """
        Expire investment if approval period has passed[citation:1]
        """
        if investment.status != Investment.Status.APPROVED:
            return
        
        if not investment.approval_expires_at:
            return
        
        if investment.approval_expires_at > timezone.now():
            return
        
        investment.status = Investment.Status.EXPIRED
        investment.save()
        
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=None,  # System action
            action_type=InvestmentAuditLog.ActionType.EXPIRED,
            description='Investment approval expired',
            previous_status=Investment.Status.APPROVED,
            new_status=Investment.Status.EXPIRED
        )
        
        send_notification(
            recipients=[investment.investor],
            notification_type='INVESTMENT_EXPIRED',
            title='Investment Expired',
            message=f'Your investment request for {investment.project.title} has expired',
            related_object=investment
        )
    
    @staticmethod
    @transaction.atomic
    def cancel_investment(investment: Investment, actor: User) -> Investment:
        """
        Cancel investment request[citation:7]
        SRS: Investors can cancel pending investments
        """
        if investment.status not in [Investment.Status.REQUESTED, Investment.Status.APPROVED]:
            raise ValidationError('Investment cannot be cancelled in current status')
        
        if actor != investment.investor and not actor.is_admin:
            raise PermissionDenied('Only investor or admin can cancel investment')
        
        previous_status = investment.status
        investment.status = Investment.Status.CANCELLED
        investment.save()
        
        # Cancel any pending payments
        pending_payments = investment.payments.filter(
            status=PaymentTransaction.Status.PENDING
        )
        for payment in pending_payments:
            payment.status = PaymentTransaction.Status.CANCELLED
            payment.save()
        
        InvestmentAuditLog.objects.create(
            investment=investment,
            actor=actor,
            action_type=InvestmentAuditLog.ActionType.CANCELLED,
            description='Investment cancelled',
            previous_status=previous_status,
            new_status=Investment.Status.CANCELLED,
            metadata={'cancelled_by': actor.email}
        )
        
        send_notification(
            recipients='admins',
            notification_type='INVESTMENT_CANCELLED',
            title='Investment Cancelled',
            message=f'{actor.email} cancelled investment in {investment.project.title}',
            related_object=investment
        )
        
        return investment


class InvestmentAnalyticsService:
    """Service for investment analytics and reporting"""
    
    @staticmethod
    def get_investor_portfolio(investor: User) -> Dict[str, Any]:
        """Get investor's investment portfolio summary"""
        investments = Investment.objects.filter(
            investor=investor,
            status=Investment.Status.COMPLETED
        ).select_related('project')
        
        total_invested = sum(inv.total_amount for inv in investments)
        total_shares = sum(inv.shares for inv in investments)
        
        return {
            'total_investments': investments.count(),
            'total_invested': float(total_invested),
            'total_shares': total_shares,
            'active_projects': investments.values('project').distinct().count(),
            'portfolio_value': float(total_invested),  # In real scenario, calculate current value
            'investments': [
                {
                    'project_id': str(inv.project.id),
                    'project_title': inv.project.title,
                    'shares': inv.shares,
                    'invested_amount': float(inv.total_amount),
                    'investment_date': inv.completed_at.isoformat() if inv.completed_at else None,
                    'current_value': float(inv.total_amount)  # Simplified
                }
                for inv in investments
            ]
        }
    
    @staticmethod
    def get_project_investment_stats(project: Project) -> Dict[str, Any]:
        """Get investment statistics for a project"""
        investments = project.investments.filter(
            status=Investment.Status.COMPLETED
        ).select_related('investor')
        
        total_investors = investments.values('investor').distinct().count()
        total_invested = sum(inv.total_amount for inv in investments)
        
        return {
            'total_investments': investments.count(),
            'total_investors': total_investors,
            'total_funding': float(total_invested),
            'average_investment': float(total_invested / investments.count()) if investments.count() > 0 else 0,
            'funding_progress': project.funding_progress,
            'recent_investments': [
                {
                    'investor_name': inv.investor.get_full_name(),
                    'shares': inv.shares,
                    'amount': float(inv.total_amount),
                    'date': inv.completed_at.isoformat() if inv.completed_at else None
                }
                for inv in investments.order_by('-completed_at')[:10]
            ]
        }