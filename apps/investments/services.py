from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from .models import SharePurchase, PaymentTransaction
from apps.projects.models import Project
from apps.audit.services import log_admin_action


def initiate_investment(project, investor, shares_requested, idempotency_key):
    """
    Initiate a new investment with idempotency.
    Returns payment info for gateway.
    """
    from django.db import IntegrityError

    # Ensure idempotency
    if PaymentTransaction.objects.filter(reference_id=idempotency_key).exists():
        raise ValidationError("Duplicate payment request detected")

    if shares_requested <= 0:
        raise ValidationError("Shares requested must be greater than zero")

    with transaction.atomic():
        # Lock project row to prevent overselling
        project = Project.objects.select_for_update().get(id=project.id)

        if project.shares_sold + shares_requested > project.total_shares:
            raise ValidationError("Not enough shares available")

        total_amount = Decimal(shares_requested) * project.share_price

        # Create payment record
        payment = PaymentTransaction.objects.create(
            reference_id=idempotency_key,
            status='INITIATED'
        )

        # Return payment info to initiate gateway payment
        return {
            'payment_id': payment.id,
            'total_amount': total_amount,
            'shares_requested': shares_requested
        }


def confirm_payment(payment_reference_id, gateway_payload, admin_user, success=True):
    """
    Confirm payment from gateway. Update SharePurchase & Project.shares_sold.
    Logs audit.
    """
    payment = PaymentTransaction.objects.select_for_update().get(reference_id=payment_reference_id)

    if payment.status != 'INITIATED':
        raise ValidationError("Payment already processed")

    payment.raw_payload = gateway_payload

    if success:
        payment.status = 'SUCCESS'
        payment.save(update_fields=['status', 'raw_payload'])

        with transaction.atomic():
            # Extract data from gateway_payload
            project_id = gateway_payload['project_id']
            investor_id = gateway_payload['investor_id']
            shares = gateway_payload['shares']

            project = Project.objects.select_for_update().get(id=project_id)
            if project.shares_sold + shares > project.total_shares:
                raise ValidationError("Oversell detected")

            SharePurchase.objects.create(
                investor_id=investor_id,
                project=project,
                shares_purchased=shares,
                price_per_share=project.share_price,
                total_amount=shares * project.share_price,
                payment=payment
            )

            project.shares_sold = F('shares_sold') + shares
            project.save(update_fields=['shares_sold'])

        # Audit log
        log_admin_action(
            admin_user=admin_user,
            action="Confirmed Payment & Share Purchase",
            entity_type="PaymentTransaction",
            entity_id=payment.id,
            metadata={
                "project_id": str(project.id),
                "investor_id": str(investor_id),
                "shares": shares,
                "total_amount": str(payment_reference_id)
            }
        )
    else:
        payment.status = 'FAILED'
        payment.save(update_fields=['status', 'raw_payload'])

        # Audit log
        log_admin_action(
            admin_user=admin_user,
            action="Payment Failed",
            entity_type="PaymentTransaction",
            entity_id=payment.id,
            metadata={
                "project_id": str(gateway_payload.get('project_id')),
                "investor_id": str(gateway_payload.get('investor_id')),
                "shares": gateway_payload.get('shares'),
                "reason": "Gateway failure"
            }
        )