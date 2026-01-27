# apps/audit/services.py

from apps.audit.models import AuditLog

def log_admin_action(actor, action, entity_type, entity_id, metadata=None):
    """
    Record an immutable audit log.
    
    Supports both user-triggered actions and webhook/system actions.
    
    Args:
        actor: User instance performing the action. None for webhook/system actions.
        action: str, e.g., "Approved Project", "PAYMENT_SUCCESS"
        entity_type: str, e.g., "Project", "SharePurchase"
        entity_id: UUID of the entity
        metadata: optional dict, e.g., {"reason": "Incomplete docs"}
    """
    AuditLog.objects.create(
        actor=actor,  # None is allowed for webhook actions
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata or {}
    )
