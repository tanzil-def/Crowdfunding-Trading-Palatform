from decimal import Decimal
from django.db import transaction
from django.db.models import F, Sum, Count
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import SharePurchase, PaymentTransaction
from apps.projects.models import Project
from utils.exceptions import UnverifiedUserError, ResourceConflictError

from apps.audit.services import log_admin_action
from apps.notifications.services import create_notification


# Configuration
PAYMENT_GATEWAY_BASE_URL = "https://sandbox.payment.gateway/pay"


def get_payment_url(reference_id: str) -> str:
    """
    Generate payment gateway URL for given reference ID.
    
    Args:
        reference_id: Unique transaction reference ID
        
    Returns:
        Complete payment URL for gateway redirect
    """
    return f"{PAYMENT_GATEWAY_BASE_URL}?ref={reference_id}"


def validate_investor_eligibility(investor):
    """
    Validate investor meets requirements to invest.
    
    SRS Requirements:
    - Unverified investors shall not be able to invest (403 Forbidden)
    - Only users with INVESTOR role can purchase shares
    
    Raises:
        UnverifiedUserError: If email is not verified (403)
        ValidationError: If user is not an investor (400)
    """
    if not investor.is_email_verified:
        raise UnverifiedUserError(
            "Email verification required. Please verify your email before investing."
        )
    
    if investor.role != 'INVESTOR':
        raise ValidationError(
            "Only investors can purchase shares."
        )


def validate_project_eligibility(project):
    """
    Validate project is eligible for investment.
    
    SRS Requirements:
    - Only approved projects can receive investments
    
    Raises:
        ValidationError: If project is not approved (400)
    """
    if project.status != 'APPROVED':
        raise ValidationError(
            f"This project is not available for investment. Status: {project.get_status_display()}"
        )


def calculate_investment_amount(project, shares_requested):
    """
    Calculate total investment amount using Decimal for precision.
    
    SRS Requirements:
    - Investment Amount = Shares × Per Share Price
    - Use Decimal to avoid floating-point errors
    
    Args:
        project: Project instance
        shares_requested: Number of shares to purchase
        
    Returns:
        Decimal: Total investment amount
        
    Raises:
        ValidationError: If shares_requested is invalid
    """
    if shares_requested <= 0:
        raise ValidationError("Number of shares must be greater than zero.")
    
    total_amount = Decimal(shares_requested) * project.share_price
    return total_amount


def check_share_availability(project, shares_requested):
    """
    Check if requested shares are available.
    
    SRS Requirements:
    - Prevent overselling under any circumstance
    - Atomic check with database lock
    
    Args:
        project: Project instance (should be locked with select_for_update)
        shares_requested: Number of shares requested
        
    Raises:
        ValidationError: If insufficient shares available (400)
    """
    shares_remaining = project.total_shares - project.shares_sold
    
    if shares_requested > shares_remaining:
        raise ValidationError(
            f"Insufficient shares available. Requested: {shares_requested}, "
            f"Available: {shares_remaining}"
        )


def initiate_investment(project, investor, shares_requested, idempotency_key):
    """
    Initiate investment process and create payment transaction.
    
    SRS Requirements Implemented:
    - Email verification enforcement (403 if unverified)
    - Only approved projects (400 if not approved)
    - Share availability check (400 if insufficient)
    - Idempotency to prevent duplicates (409 if duplicate)
    - Atomic transaction with database lock
    - Per-share price calculation using Decimal
    - Return payment_url and reference_id for gateway redirect
    
    Args:
        project: Project to invest in
        investor: User making the investment
        shares_requested: Number of shares to purchase
        idempotency_key: Unique key to prevent duplicate transactions
        
    Returns:
        dict: Payment information including payment_url and reference_id
        
    Raises:
        UnverifiedUserError: If investor email not verified (403)
        ValidationError: If validation fails (400)
        ResourceConflictError: If duplicate transaction (409)
    """
    # Validate investor eligibility
    validate_investor_eligibility(investor)
    
    # Validate project eligibility
    validate_project_eligibility(project)
    
    # Atomic transaction with database lock
    with transaction.atomic():
        # Lock project row to prevent race conditions
        project_locked = Project.objects.select_for_update().get(id=project.id)
        
        # Check share availability
        check_share_availability(project_locked, shares_requested)
        
        # Calculate total amount
        total_amount = calculate_investment_amount(project_locked, shares_requested)
        
        # Check idempotency - prevent duplicate transactions
        if PaymentTransaction.objects.filter(reference_id=idempotency_key).exists():
            raise ResourceConflictError(
                f"Transaction with reference {idempotency_key} already exists."
            )

        # Create payment transaction
        payment = PaymentTransaction.objects.create(
            reference_id=idempotency_key,
            investor=investor,
            project=project_locked,
            amount=total_amount,
            shares_requested=shares_requested,
            status=PaymentTransaction.STATUS_INITIATED
        )
        
        # Create notification for investor
        create_notification(
            user=investor,
            notification_type='INVESTMENT_INITIATED',
            title='Investment Initiated',
            message=f'Your investment of {shares_requested} shares in "{project_locked.title}" has been initiated.',
            metadata={
                'project_id': str(project_locked.id),
                'shares': shares_requested,
                'amount': str(total_amount),
                'payment_reference': idempotency_key
            }
        )
        
        # Generate payment URL
        payment_url = get_payment_url(idempotency_key)
        
        # Return response matching InvestmentInitiateResponseSerializer
        return {
            'project_id': str(project_locked.id),
            'shares_requested': shares_requested,
            'idempotency_key': idempotency_key,
            'reference_id': str(payment.id),
            'payment_url': payment_url
        }


def process_successful_payment(payment, gateway_payload, shares_requested):
    """
    Process successful payment and create share purchase.
    
    SRS Requirements Implemented:
    - Atomic share allocation with select_for_update
    - Prevent overselling under concurrency
    - Create purchase record
    - Update project shares_sold using F() expression
    - Audit logging
    - Notification to investor and developer
    
    Args:
        payment: PaymentTransaction instance (locked)
        gateway_payload: Raw payload from payment gateway
        shares_requested: Number of shares to allocate
        
    Returns:
        SharePurchase: Created share purchase instance
        
    Raises:
        ValidationError: If shares no longer available (race condition)
    """
    with transaction.atomic():
        # Lock project row to prevent race conditions
        project = Project.objects.select_for_update().get(id=payment.project.id)
        
        # Re-check share availability (critical for race condition prevention)
        check_share_availability(project, shares_requested)
        
        # Create share purchase record
        share_purchase = SharePurchase.objects.create(
            investor=payment.investor,
            project=project,
            payment=payment,
            shares_purchased=shares_requested,
            price_per_share=project.share_price,
            total_amount=payment.amount
        )
        
        # Update project shares_sold atomically using F() expression
        project.shares_sold = F('shares_sold') + shares_requested
        project.save(update_fields=['shares_sold'])
        
        # Update payment status
        payment.status = PaymentTransaction.STATUS_SUCCESS
        payment.gateway_payload = gateway_payload
        payment.processed_at = timezone.now()
        payment.save(update_fields=['status', 'gateway_payload', 'processed_at'])
        
        # Refresh project to get updated shares_sold value
        project.refresh_from_db()
        
        # Notify investor of successful payment
        create_notification(
            user=payment.investor,
            notification_type='PAYMENT_SUCCESS',
            title='Investment Successful',
            message=f'You have successfully purchased {shares_requested} shares in "{project.title}".',
            metadata={
                'project_id': str(project.id),
                'share_purchase_id': str(share_purchase.id),
                'shares': shares_requested,
                'amount': str(payment.amount)
            }
        )
        
        # Notify developer of new investment
        create_notification(
            user=project.developer,
            notification_type='NEW_INVESTMENT',
            title='New Investment Received',
            message=f'{payment.investor.email} invested in your project "{project.title}".',
            metadata={
                'project_id': str(project.id),
                'investor_id': str(payment.investor.id),
                'shares': shares_requested,
                'amount': str(payment.amount)
            }
        )
        
        # Create audit log
        log_admin_action(
            admin_user=None,
            action='PAYMENT_SUCCESS',
            entity_type='SharePurchase',
            entity_id=str(share_purchase.id),
            metadata={
                'payment_reference': payment.reference_id,
                'project_id': str(project.id),
                'investor_id': str(payment.investor.id),
                'shares_purchased': shares_requested,
                'total_amount': str(payment.amount),
                'shares_remaining': project.total_shares - project.shares_sold
            }
        )
        
        return share_purchase


def process_failed_payment(payment, gateway_payload, failure_reason=None):
    """
    Process failed payment.
    
    SRS Requirements Implemented:
    - Failed payments do not allocate shares
    - Audit logging for failures
    - User notification
    
    Args:
        payment: PaymentTransaction instance
        gateway_payload: Raw payload from payment gateway
        failure_reason: Optional reason for failure
    """
    payment.status = PaymentTransaction.STATUS_FAILED
    payment.gateway_payload = gateway_payload
    payment.failure_reason = failure_reason or "Payment gateway reported failure"
    payment.processed_at = timezone.now()
    payment.save(update_fields=['status', 'gateway_payload', 'failure_reason', 'processed_at'])
    
    # Notify investor of payment failure
    create_notification(
        user=payment.investor,
        notification_type='PAYMENT_FAILED',
        title='Payment Failed',
        message=f'Your payment for {payment.project.title} could not be processed. Please try again.',
        metadata={
            'project_id': str(payment.project.id),
            'payment_reference': payment.reference_id,
            'amount': str(payment.amount),
            'reason': payment.failure_reason
        }
    )
    
    # Create audit log
    log_admin_action(
        admin_user=None,
        action='PAYMENT_FAILED',
        entity_type='PaymentTransaction',
        entity_id=str(payment.id),
        metadata={
            'payment_reference': payment.reference_id,
            'project_id': str(payment.project.id),
            'investor_id': str(payment.investor.id),
            'amount': str(payment.amount),
            'failure_reason': payment.failure_reason
        }
    )


def confirm_payment(payment_reference_id, gateway_payload, success=True):
    """
    Main payment confirmation handler for gateway callbacks.
    
    SRS Requirements Implemented:
    - Idempotent payment processing (409 if already processed)
    - Prevents duplicate callbacks
    - Atomic transactions with select_for_update
    - Comprehensive audit trail
    - Race condition protection
    
    Args:
        payment_reference_id: Reference ID from payment gateway
        gateway_payload: Raw payload from payment gateway
        success: Whether payment was successful
        
    Returns:
        dict: Processing result with status and details
        
    Raises:
        ValidationError: If payment not found (404)
        ResourceConflictError: If already processed (409)
    """
    with transaction.atomic():
        # Lock payment transaction to prevent duplicate processing
        try:
            payment = PaymentTransaction.objects.select_for_update().get(
                reference_id=payment_reference_id
            )
        except PaymentTransaction.DoesNotExist:
            raise ValidationError(f"Payment transaction not found: {payment_reference_id}")
        
        # Idempotency check - prevent duplicate callback processing
        if payment.status != PaymentTransaction.STATUS_INITIATED:
            raise ResourceConflictError(
                f"Payment already processed with status: {payment.get_status_display()}"
            )
        
        # Get shares_requested from gateway payload or payment record
        shares_requested = gateway_payload.get('shares_requested') or payment.shares_requested
        if not shares_requested:
            raise ValidationError("Gateway payload missing 'shares_requested' field")
        
        if success:
            # Process successful payment
            share_purchase = process_successful_payment(
                payment=payment,
                gateway_payload=gateway_payload,
                shares_requested=shares_requested
            )
            return {
                'status': 'success',
                'share_purchase_id': str(share_purchase.id),
                'shares_purchased': share_purchase.shares_purchased,
                'message': 'Payment confirmed and shares allocated successfully'
            }
        else:
            # Process failed payment
            failure_reason = gateway_payload.get('failure_reason', 'Gateway reported failure')
            process_failed_payment(
                payment=payment,
                gateway_payload=gateway_payload,
                failure_reason=failure_reason
            )
            return {
                'status': 'failed',
                'message': 'Payment failed, no shares allocated'
            }


def get_investor_portfolio_summary(investor):
    """
    Get investor's portfolio summary using optimized aggregation queries.
    
    SRS Requirements:
    - Total invested amount
    - Number of projects invested
    - Total shares owned
    - Investment count
    
    Args:
        investor: User instance
        
    Returns:
        dict: Portfolio summary with aggregated statistics
    """
    # Use aggregation for performance (single query instead of multiple)
    summary = SharePurchase.objects.filter(investor=investor).aggregate(
        total_invested=Sum('total_amount'),
        total_shares=Sum('shares_purchased'),
        investment_count=Count('id'),
        projects_count=Count('project', distinct=True)
    )
    
    return {
        'total_invested': summary['total_invested'] or Decimal('0.00'),
        'projects_invested': summary['projects_count'] or 0,
        'total_shares_owned': summary['total_shares'] or 0,
        'investment_count': summary['investment_count'] or 0
    }