from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.audit.services import log_admin_action

def approve_access_request(access_request, admin_user):
    if access_request.status != 'PENDING':
        raise ValidationError("Only pending requests can be approved")
    access_request.status = 'APPROVED'
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'decided_by'])

    # Notify investor via event hook
    from apps.notifications.services import notify_investor_access_approved
    notify_investor_access_approved(access_request)

    log_admin_action(
        admin_user=admin_user,
        action="Approved Access Request",
        entity_type="AccessRequest",
        entity_id=access_request.id,
        metadata={
            "project_title": access_request.project.title,
            "investor_email": access_request.investor.email
        }
    )

def reject_access_request(access_request, admin_user, reason=None):
    if access_request.status != 'PENDING':
        raise ValidationError("Only pending requests can be rejected")
    access_request.status = 'REJECTED'
    access_request.reason = reason
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'reason', 'decided_by'])

    # Notify investor via event hook
    from apps.notifications.services import notify_investor_access_rejected
    notify_investor_access_rejected(access_request, reason)

    log_admin_action(
        admin_user=admin_user,
        action="Rejected Access Request",
        entity_type="AccessRequest",
        entity_id=access_request.id,
        metadata={
            "project_title": access_request.project.title,
            "investor_email": access_request.investor.email,
            "reason": reason
        }
    )

def revoke_access_request(access_request, admin_user, reason=None):
    if access_request.status != 'APPROVED':
        raise ValidationError("Only approved requests can be revoked")
    access_request.status = 'REVOKED'
    access_request.reason = reason
    access_request.decided_by = admin_user
    access_request.save(update_fields=['status', 'reason', 'decided_by'])

    # Notify investor via event hook
    from apps.notifications.services import notify_investor_access_revoked
    notify_investor_access_revoked(access_request, admin_user)

    log_admin_action(
        admin_user=admin_user,
        action="Revoked Access",
        entity_type="AccessRequest",
        entity_id=access_request.id,
        metadata={
            "project_title": access_request.project.title,
            "investor_email": access_request.investor.email,
            "reason": reason
        }
    )

