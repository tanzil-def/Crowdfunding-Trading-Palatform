from decimal import Decimal
import uuid
from django.db import transaction
from django.db.models import F, Sum, Count
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import InvestmentRequest, PaymentTransaction, PortfolioHolding, ShareLedger, SharePurchase
from apps.projects.models import Project
from apps.audit.services import log_admin_action
from apps.notifications.services import create_notification
from utils.exceptions import UnverifiedUserError, ResourceConflictError

# Configuration
PAYMENT_GATEWAY_BASE_URL = "https://sandbox.payment.gateway/pay"


def initiate_investment(project, investor, shares_requested):
    """
    Step 1: Investor initiates investment.
    Creates an InvestmentRequest in PENDING_PAYMENT status.
    """
    if not investor.is_email_verified:
        raise UnverifiedUserError("Email verification required.")
    
    if investor.role != 'INVESTOR':
        raise ValidationError("Only investors can purchase shares.")
    
    if project.status != 'APPROVED':
        raise ValidationError("Project is not available for investment.")

    with transaction.atomic():
        # Inventory check (optimistic here, strict check happens at admin approval)
        shares_remaining = project.total_shares - project.shares_sold
        if shares_requested > shares_remaining:
            raise ValidationError(f"Insufficient shares. Available: {shares_remaining}")

        amount = Decimal(shares_requested) * project.share_price
        payment_reference = f"INV-{uuid.uuid4().hex[:8].upper()}"

        # Create InvestmentRequest
        investment_request = InvestmentRequest.objects.create(
            investor=investor,
            project=project,
            requested_shares=shares_requested,
            price_per_share=project.share_price,
            amount=amount,
            status=InvestmentRequest.STATUS_PENDING_PAYMENT,
            payment_reference=payment_reference,
            payment_url=f"{PAYMENT_GATEWAY_BASE_URL}?ref={payment_reference}"
        )

        log_admin_action(
            actor=investor,
            action='INVESTMENT_INITIATED',
            entity_type='InvestmentRequest',
            entity_id=investment_request.id,
            metadata={'shares': shares_requested, 'amount': str(amount)}
        )

        return investment_request


def confirm_payment(payment_reference, gateway_payload, success=True):
    """
    Step 2: Gateway callback confirms payment.
    Updates InvestmentRequest to PAYMENT_CONFIRMED.
    """
    with transaction.atomic():
        try:
            investment_request = InvestmentRequest.objects.select_for_update().get(payment_reference=payment_reference)
        except InvestmentRequest.DoesNotExist:
            raise ValidationError("Investment request not found.")

        if investment_request.status != InvestmentRequest.STATUS_PENDING_PAYMENT:
            raise ResourceConflictError(f"Request already processed. Current status: {investment_request.status}")

        # Create PaymentTransaction log
        PaymentTransaction.objects.create(
            investment_request=investment_request,
            gateway_transaction_id=gateway_payload.get('txn_id'),
            amount=investment_request.amount,
            status=PaymentTransaction.STATUS_SUCCESS if success else PaymentTransaction.STATUS_FAILED,
            raw_gateway_response=gateway_payload
        )

        if success:
            investment_request.status = InvestmentRequest.STATUS_PAYMENT_CONFIRMED
            message = "Payment confirmed. Awaiting admin approval."
            action = 'PAYMENT_CONFIRMED'
        else:
            investment_request.status = InvestmentRequest.STATUS_PAYMENT_FAILED
            message = "Payment failed."
            action = 'PAYMENT_FAILED'

        investment_request.save(update_fields=['status', 'updated_at'])

        log_admin_action(
            actor=None,
            action=action,
            entity_type='InvestmentRequest',
            entity_id=investment_request.id,
            metadata={'gateway_payload': gateway_payload}
        )

        # Notify investor
        create_notification(
            user=investment_request.user if hasattr(investment_request, 'user') else investment_request.investor,
            notification_type='INVESTMENT_PAYMENT_UPDATE',
            title='Payment Update',
            message=f"Your payment for {investment_request.project.title} has been {action.lower()}.",
            metadata={'request_id': str(investment_request.id)}
        )

        return investment_request


def process_admin_investment_action(investment_request_id, admin_user, action, admin_remarks=None):
    """
    Step 3: Admin approves/rejects confirmed payment.
    Strict inventory deduction happens here.
    """
    if action not in ['APPROVE', 'REJECT']:
        raise ValidationError("Invalid action. Must be APPROVE or REJECT.")

    with transaction.atomic():
        # Lock both project and request
        investment_request = InvestmentRequest.objects.select_for_update().get(id=investment_request_id)
        project = Project.objects.select_for_update().get(id=investment_request.project_id)

        if investment_request.status != InvestmentRequest.STATUS_PAYMENT_CONFIRMED:
            raise ValidationError(f"Only PAYMENT_CONFIRMED requests can be processed. Current: {investment_request.status}")

        before_state = {'status': investment_request.status, 'project_shares_sold': project.shares_sold}

        if action == 'APPROVE':
            # STRICT INVENTORY CHECK
            shares_requested = investment_request.requested_shares
            shares_available = project.total_shares - project.shares_sold
            
            if shares_requested > shares_available:
                investment_request.status = InvestmentRequest.STATUS_ADMIN_REJECTED
                investment_request.admin_remarks = f"Automatic rejection: Insufficient inventory. {admin_remarks or ''}"
                investment_request.save()
                raise ValidationError("Insufficient shares available to fulfill this request.")

            # 1. Deduct shares from Project
            project.shares_sold = F('shares_sold') + shares_requested
            project.save(update_fields=['shares_sold'])

            # 2. Update InvestmentRequest status
            investment_request.status = InvestmentRequest.STATUS_SHARES_ALLOCATED
            investment_request.admin_remarks = admin_remarks
            investment_request.save()

            # 3. Create ShareLedger (Immutable entry)
            ShareLedger.objects.create(
                investment_request=investment_request,
                investor=investment_request.investor,
                project=project,
                shares_delta=shares_requested,
                reason=ShareLedger.REASON_PURCHASE
            )

            # 4. Update PortfolioHolding
            holding, created = PortfolioHolding.objects.get_or_create(
                investor=investment_request.investor,
                project=project
            )
            # Recalculate average price
            total_shares_before = holding.shares_owned
            new_shares = shares_requested
            total_shares_after = total_shares_before + new_shares
            
            total_cost_before = holding.avg_buy_price * total_shares_before
            new_cost = investment_request.amount
            
            holding.shares_owned = total_shares_after
            holding.avg_buy_price = (total_cost_before + new_cost) / total_shares_after
            holding.save()

            # 5. Create SharePurchase (History/Receipt)
            SharePurchase.objects.create(
                investor=investment_request.investor,
                project=project,
                investment_request=investment_request,
                shares_purchased=shares_requested,
                price_per_share=investment_request.price_per_share,
                total_amount=investment_request.amount
            )

            log_action = 'ADMIN_APPROVED_INVESTMENT'
            notif_msg = f"Your investment in {project.title} has been approved and shares allocated."
        else:
            # REJECT
            investment_request.status = InvestmentRequest.STATUS_ADMIN_REJECTED
            investment_request.admin_remarks = admin_remarks
            investment_request.save()
            
            log_action = 'ADMIN_REJECTED_INVESTMENT'
            notif_msg = f"Your investment in {project.title} has been rejected. Reason: {admin_remarks}"

        project.refresh_from_db()
        after_state = {'status': investment_request.status, 'project_shares_sold': project.shares_sold}

        # Audit Log
        log_admin_action(
            actor=admin_user,
            action=log_action,
            entity_type='InvestmentRequest',
            entity_id=investment_request.id,
            metadata={'admin_remarks': admin_remarks},
            before_state=before_state,
            after_state=after_state
        )

        # Notify Investor
        create_notification(
            user=investment_request.investor,
            notification_type='INVESTMENT_FINALIZED',
            title='Investment Update',
            message=notif_msg,
            metadata={'request_id': str(investment_request.id), 'status': investment_request.status}
        )

        return investment_request


def get_investor_portfolio_summary(investor):
    """
    Get aggregated summary from PortfolioHolding.
    """
    summary = PortfolioHolding.objects.filter(investor=investor).aggregate(
        total_invested=Sum(F('shares_owned') * F('avg_buy_price')),
        total_shares=Sum('shares_owned'),
        projects_count=Count('project', distinct=True)
    )
    
    return {
        'total_invested': summary['total_invested'] or Decimal('0.00'),
        'projects_invested': summary['projects_count'] or 0,
        'total_shares_owned': summary['total_shares'] or 0,
        'investment_count': InvestmentRequest.objects.filter(investor=investor, status='SHARES_ALLOCATED').count()
    }