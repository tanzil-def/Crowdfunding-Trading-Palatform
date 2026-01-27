import uuid
from django.db import models
from apps.users.models import User

class AuditLog(models.Model):
    """
    Audit log for tracking system actions.
    
    actor field is nullable to support webhook-triggered actions (no user context).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  
        null=True,                  
        blank=True,
        related_name='audit_logs',
        help_text="User who performed action. None for webhook/system actions."
    )
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    before_state = models.JSONField(null=True, blank=True, help_text="State of entity before action")
    after_state = models.JSONField(null=True, blank=True, help_text="State of entity after action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.email} -> {self.action} on {self.entity_type} ({self.entity_id})"
