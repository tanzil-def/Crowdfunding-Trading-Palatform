from .models import Notification
from apps.users.models import User
from django.db import transaction
from django.utils import timezone
import json

def create_notification(user, notification_type, message, title=None, metadata=None):
    """
    Central function to create notifications for any user.
    
    Args:
        user: User instance to notify
        notification_type: String from NOTIFICATION_TYPE_CHOICES
        message: Human-readable notification message
        title: Optional title for the notification
        metadata: Optional dict with event-specific data (project_id, investor_id, etc.)
    
    Returns:
        Notification instance
    """
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        metadata=metadata or {}
    )
    
    # Broadcast to user via WebSocket
    from .websocket_utils import broadcast_notification
    broadcast_notification(user.id, notification)
    
    return notification


def mark_notification_as_read(notification):
    """Mark a notification as read. Idempotent operation."""
    notification.is_read = True
    notification.save(update_fields=['is_read'])


@transaction.atomic
def notify_admins_project_submitted(project):
    """
    Notify all admins that a developer submitted a new project.
    
    Called from: projects.services.submit_project_for_review()
    """
    admins = User.objects.filter(role='ADMIN', is_active=True)
    
    for admin in admins:
        create_notification(
            user=admin,
            notification_type='PROJECT_SUBMITTED',
            title='New Project Submission',
            message=f"Developer '{project.developer.email}' submitted project '{project.title}' for review.",
            metadata={
                'project_id': str(project.id),
                'project_title': project.title,
                'developer_id': str(project.developer.id),
                'developer_email': project.developer.email,
            }
        )


@transaction.atomic
def notify_developer_project_approved(project, admin):
    """
    Notify developer that their project was approved.
    
    Called from: projects.services.admin_approve_project()
    """
    create_notification(
        user=project.developer,
        notification_type='PROJECT_APPROVED',
        title='Project Approved',
        message=f"Your project '{project.title}' has been approved by admin {admin.email}. It is now live!",
        metadata={
            'project_id': str(project.id),
            'project_title': project.title,
            'approved_by': admin.email,
            'approved_at': str(project.updated_at),
        }
    )


@transaction.atomic
def notify_developer_project_rejected(project, admin, reason=None):
    """
    Notify developer that their project was rejected.
    
    Called from: projects.services.admin_reject_project()
    """
    message = f"Your project '{project.title}' has been rejected by admin {admin.email}."
    if reason:
        message += f" Reason: {reason}"
    
    create_notification(
        user=project.developer,
        notification_type='PROJECT_REJECTED',
        title='Project Rejected',
        message=message,
        metadata={
            'project_id': str(project.id),
            'project_title': project.title,
            'rejected_by': admin.email,
            'reason': reason,
            'rejected_at': str(project.updated_at),
        }
    )


@transaction.atomic
def notify_developer_project_changes_requested(project, admin, changes=None):
    """
    Notify developer that changes are requested for their project.
    
    Called from: projects.services.admin_request_changes()
    """
    message = f"Admin {admin.email} requested changes to your project '{project.title}'."
    if changes:
        message += f" Feedback: {changes}"
    
    create_notification(
        user=project.developer,
        notification_type='PROJECT_CHANGES_REQUESTED',
        title='Project Changes Requested',
        message=message,
        metadata={
            'project_id': str(project.id),
            'project_title': project.title,
            'requested_by': admin.email,
            'changes': changes,
            'requested_at': str(project.updated_at),
        }
    )


@transaction.atomic
def notify_investor_payment_success(investor, payment_transaction):
    """
    Notify investor that their payment was successfully processed.
    
    Called from: investments.services.confirm_payment()
    """
    from apps.investments.models import PaymentTransaction
    
    project = payment_transaction.project
    shares = payment_transaction.shares_requested
    
    create_notification(
        user=investor,
        notification_type='PAYMENT_SUCCESS',
        title='Payment Confirmed',
        message=f"Your payment for {shares} shares in project '{project.title}' has been confirmed. Status: {payment_transaction.status}",
        metadata={
            'payment_id': str(payment_transaction.id),
            'project_id': str(project.id),
            'project_title': project.title,
            'shares': shares,
            'amount': str(payment_transaction.amount),
            'status': payment_transaction.status,
            'confirmed_at': str(payment_transaction.updated_at),
        }
    )


@transaction.atomic
def notify_investor_payment_failed(investor, payment_transaction, reason=None):
    """
    Notify investor that their payment failed.
    
    Called from: investments.services.confirm_payment() or payment gateway
    """
    project = payment_transaction.project
    message = f"Your payment for project '{project.title}' has failed."
    
    if reason:
        message += f" Reason: {reason}"
    
    create_notification(
        user=investor,
        notification_type='PAYMENT_FAILED',
        title='Payment Failed',
        message=message,
        metadata={
            'payment_id': str(payment_transaction.id),
            'project_id': str(project.id),
            'project_title': project.title,
            'amount': str(payment_transaction.amount),
            'reason': reason,
            'failed_at': str(payment_transaction.updated_at),
        }
    )


@transaction.atomic
def notify_admin_access_request_received(access_request):
    """
    Notify admin(s) that an investor requested access to restricted fields.
    
    Called from: access_requests.services.create_access_request()
    """
    admins = User.objects.filter(role='ADMIN', is_active=True)
    project = access_request.project
    investor = access_request.investor
    
    for admin in admins:
        create_notification(
            user=admin,
            notification_type='ACCESS_REQUESTED',
            title='Restricted Access Request',
            message=f"Investor '{investor.email}' requested access to restricted data for project '{project.title}'.",
            metadata={
                'access_request_id': str(access_request.id),
                'project_id': str(project.id),
                'project_title': project.title,
                'investor_id': str(investor.id),
                'investor_email': investor.email,
                'requested_at': str(access_request.created_at),
            }
        )


@transaction.atomic
def notify_investor_access_approved(access_request):
    """
    Notify investor that their access request was approved.
    
    Called from: access_requests.services.approve_access_request()
    """
    investor = access_request.investor
    project = access_request.project
    
    create_notification(
        user=investor,
        notification_type='ACCESS_APPROVED',
        title='Access Granted',
        message=f"Your request for access to restricted data on project '{project.title}' has been approved.",
        metadata={
            'access_request_id': str(access_request.id),
            'project_id': str(project.id),
            'project_title': project.title,
            'approved_at': str(timezone.now()),
        }
    )


@transaction.atomic
def notify_investor_access_rejected(access_request, reason=None):
    """
    Notify investor that their access request was rejected.
    
    Called from: access_requests.services.reject_access_request()
    """
    investor = access_request.investor
    project = access_request.project
    
    message = f"Your request for access to restricted data on project '{project.title}' has been rejected."
    if reason:
        message += f" Reason: {reason}"
    
    create_notification(
        user=investor,
        notification_type='ACCESS_REJECTED',
        title='Access Denied',
        message=message,
        metadata={
            'access_request_id': str(access_request.id),
            'project_id': str(project.id),
            'project_title': project.title,
            'reason': reason,
            'rejected_at': str(timezone.now()),
        }
    )


@transaction.atomic
def notify_investor_access_revoked(access_request, revoked_by):
    """
    Notify investor that their access was revoked.
    
    Called from: access_requests.services.revoke_access_request()
    """
    investor = access_request.investor
    project = access_request.project
    
    create_notification(
        user=investor,
        notification_type='ACCESS_REVOKED',
        title='Access Revoked',
        message=f"Your access to restricted data on project '{project.title}' has been revoked by {revoked_by.email}.",
        metadata={
            'access_request_id': str(access_request.id),
            'project_id': str(project.id),
            'project_title': project.title,
            'revoked_by': revoked_by.email,
            'revoked_at': str(timezone.now()),
        }
    )

