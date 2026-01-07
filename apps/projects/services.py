# apps/projects/services.py

from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.db.models import F
from .models import Project
from apps.audit.services import log_admin_action

# ---------- Project (Phase 2) ----------
def calculate_share_price(total_value, total_shares):
    if total_shares <= 0:
        raise ValidationError("Total shares must be greater than zero")
    return Decimal(total_value) / Decimal(total_shares)

def validate_project_editable(project):
    if project.status not in ['DRAFT', 'NEEDS_CHANGES']:
        raise ValidationError("Project cannot be modified in this state")

def submit_project_for_review(project):
    if project.status != 'DRAFT':
        raise ValidationError("Only draft projects can be submitted")
    project.status = 'PENDING'
    project.save(update_fields=['status'])


# ---------- Media (Phase 3) ----------
IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']
MODEL_3D_EXTENSIONS = ['glb', 'gltf']
MAX_IMAGE_MB = 5
MAX_3D_MB = 50

def validate_media(file, media_type):
    ext = file.name.split('.')[-1].lower()
    size_mb = file.size / (1024 * 1024)

    if media_type == 'IMAGE':
        if ext not in IMAGE_EXTENSIONS:
            raise ValidationError("Unsupported image format")
        if size_mb > MAX_IMAGE_MB:
            raise ValidationError("Image file too large")

    if media_type == 'MODEL_3D':
        if ext not in MODEL_3D_EXTENSIONS:
            raise ValidationError("Unsupported 3D model format")
        if size_mb > MAX_3D_MB:
            raise ValidationError("3D model file too large")


# ---------- Admin (Phase 4) ----------
def admin_approve_project(project, admin_user):
    if project.status != 'PENDING':
        raise ValidationError("Only pending projects can be approved")
    project.status = 'APPROVED'
    project.save(update_fields=['status'])

    # Audit log
    log_admin_action(
        admin_user=admin_user,
        action="Approved Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={"title": project.title, "developer_email": project.developer.email}
    )

def admin_reject_project(project, admin_user, reason=None):
    if project.status != 'PENDING':
        raise ValidationError("Only pending projects can be rejected")
    project.status = 'REJECTED'
    project.save(update_fields=['status'])

    # Audit log
    log_admin_action(
        admin_user=admin_user,
        action="Rejected Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={"title": project.title, "developer_email": project.developer.email, "reason": reason}
    )

def admin_request_changes(project, admin_user, note=None):
    if project.status != 'PENDING':
        raise ValidationError("Only pending projects can request changes")
    project.status = 'NEEDS_CHANGES'
    project.save(update_fields=['status'])

    # Audit log
    log_admin_action(
        admin_user=admin_user,
        action="Requested Changes on Project",
        entity_type="Project",
        entity_id=project.id,
        metadata={"title": project.title, "developer_email": project.developer.email, "note": note}
    )
