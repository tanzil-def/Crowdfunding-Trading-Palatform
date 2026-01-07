import uuid
from django.db import models
from apps.users.models import User

class Notification(models.Model):

    NOTIFICATION_TYPE_CHOICES = (
        ('PROJECT', 'Project'),
        ('INVESTMENT', 'Investment'),
        ('ACCESS', 'Access Request'),
        ('SYSTEM', 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.user.email}"
