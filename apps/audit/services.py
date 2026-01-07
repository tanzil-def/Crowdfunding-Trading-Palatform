# apps/audit/services.py

from apps.audit.models import AuditLog

def log_admin_action(admin_user, action, entity_type, entity_id, metadata=None):
    """
    Record an immutable audit log.
    
    Args:
        admin_user: User instance performing the action
        action: str, e.g., "Approved Project"
        entity_type: str, e.g., "Project"
        entity_id: UUID of the entity
        metadata: optional dict, e.g., {"reason": "Incomplete docs"}
    """
    AuditLog.objects.create(
        actor=admin_user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata or {}
    )
