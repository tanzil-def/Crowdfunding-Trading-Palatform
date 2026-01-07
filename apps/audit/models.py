import uuid
from django.db import models
from apps.users.models import User

class AuditLog(models.Model):
    """
    Immutable audit log for admin actions.
    Never updated or deleted.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        limit_choices_to={'role': 'ADMIN'}  # Only admins can perform actions
    )
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.email} -> {self.action} on {self.entity_type} ({self.entity_id})"
