from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Project


IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
MODEL_3D_EXTENSIONS = ['glb', 'gltf']
MAX_IMAGE_MB = 5
MAX_3D_MB = 50


def calculate_share_price(total_value, total_shares):
    """
    Calculate per-share price from total value and share count.
    """
    if total_shares <= 0:
        raise ValidationError("Total shares must be greater than zero")
    return Decimal(total_value) / Decimal(total_shares)


def validate_project_editable(project):
    """
    Ensure project can be edited based on its current status.
    """
    if project.status not in ['DRAFT', 'NEEDS_CHANGES']:
        raise ValidationError({
            "detail": f"Project in {project.status} status cannot be modified"
        })


def validate_project_submittable(project):
    """
    Validate all required fields before submission.
    """
    if project.status != 'DRAFT':
        raise ValidationError({"detail": "Only draft projects can be submitted"})
    
    required_fields = {
        'title': project.title,
        'description': project.description,
        'category': project.category,
        'duration_days': project.duration_days,
        'total_project_value': project.total_project_value,
        'total_shares': project.total_shares,
    }
    
    missing = [field for field, value in required_fields.items() if not value]
    if missing:
        raise ValidationError({
            "detail": f"Missing required fields: {', '.join(missing)}"
        })


@transaction.atomic
def submit_project_for_review(project):
    """
    Submit project for admin review.
    """
    validate_project_submittable(project)
    project.status = 'PENDING'
    project.save(update_fields=['status'])

    # Notify admins
    from apps.notifications.services import create_notification
    from apps.users.models import User
    admins = User.objects.filter(role='ADMIN', is_active=True)
    for admin in admins:
        create_notification(
            user=admin,
            notification_type='PROJECT',
            title='New Project Submission',
            message=f"New project '{project.title}' submitted for review by {project.developer.email}."
        )


def validate_media(file, media_type):
    """
    Validate uploaded media files based on type, extension, and size.
    """
    ext = file.name.split('.')[-1].lower()
    size_mb = file.size / (1024 * 1024)
    
    if media_type == 'IMAGE':
        if ext not in IMAGE_EXTENSIONS:
            raise ValidationError({
                "file": f"Unsupported image format. Allowed: {', '.join(IMAGE_EXTENSIONS)}"
            })
        if size_mb > MAX_IMAGE_MB:
            raise ValidationError({
                "file": f"Image file too large. Maximum size: {MAX_IMAGE_MB}MB"
            })
    
    elif media_type == 'MODEL_3D':
        if ext not in MODEL_3D_EXTENSIONS:
            raise ValidationError({
                "file": f"Unsupported 3D model format. Allowed: {', '.join(MODEL_3D_EXTENSIONS)}"
            })
        if size_mb > MAX_3D_MB:
            raise ValidationError({
                "file": f"3D model file too large. Maximum size: {MAX_3D_MB}MB"
            })


@transaction.atomic
def admin_approve_project(project, admin_user):
    """
    Approve a pending project.
    """
    if project.status != 'PENDING':
        raise ValidationError({"detail": "Only pending projects can be approved"})
    
    project.status = 'APPROVED'
    project.save(update_fields=['status'])
    
    log_admin_action(
        admin_user=admin_user,
        action="Approved Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={
            "title": project.title,
            "developer_email": project.developer.email
        }
    )

    from apps.notifications.services import create_notification
    create_notification(
        user=project.developer,
        notification_type='PROJECT',
        title='Project Approved',
        message=f"Your project '{project.title}' has been approved!"
    )


@transaction.atomic
def admin_reject_project(project, admin_user, reason=None):
    """
    Reject a pending project with optional reason.
    """
    if project.status != 'PENDING':
        raise ValidationError({"detail": "Only pending projects can be rejected"})
    
    project.status = 'REJECTED'
    project.save(update_fields=['status'])
    
    log_admin_action(
        admin_user=admin_user,
        action="Rejected Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={
            "title": project.title,
            "developer_email": project.developer.email,
            "reason": reason or "No reason provided"
        }
    )

    from apps.notifications.services import create_notification
    create_notification(
        user=project.developer,
        notification_type='PROJECT',
        title='Project Rejected',
        message=f"Your project '{project.title}' was rejected. Reason: {reason or 'No reason provided'}"
    )


@transaction.atomic
def admin_request_changes(project, admin_user, note=None):
    """
    Request changes on a pending project.
    """
    if project.status != 'PENDING':
        raise ValidationError({"detail": "Only pending projects can request changes"})
    
    project.status = 'NEEDS_CHANGES'
    project.save(update_fields=['status'])
    
    log_admin_action(
        admin_user=admin_user,
        action="Requested Changes on Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={
            "title": project.title,
            "developer_email": project.developer.email,
            "note": note or "No note provided"
        }
    )

    from apps.notifications.services import create_notification
    create_notification(
        user=project.developer,
        notification_type='PROJECT',
        title='Changes Requested',
        message=f"Changes requested for project '{project.title}'. Note: {note or 'No note provided'}"
    )


def filter_restricted_fields(project_data, user, project):
    """
    Remove restricted fields from project data if user doesn't have access.
    """
    if user.role == 'ADMIN' or user == project.developer:
        return project_data
    
    if user.role == 'INVESTOR':
        from apps.access_requests.models import AccessRequest
        has_access = AccessRequest.objects.filter(
            investor=user,
            project=project,
            status='APPROVED'
        ).exists()
        
        if has_access:
            return project_data
    
    restricted = project.restricted_fields or {}
    for field in restricted.keys():
        project_data.pop(field, None)
    
    return project_data