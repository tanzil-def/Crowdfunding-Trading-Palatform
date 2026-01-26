import uuid
from django.db import models
from apps.users.models import User

class Notification(models.Model):

    # Notification type categories
    NOTIFICATION_TYPE_CHOICES = (
        # PROJECT EVENTS (for admin/developer)
        ('PROJECT_SUBMITTED', 'Project Submitted'),
        ('PROJECT_APPROVED', 'Project Approved'),
        ('PROJECT_REJECTED', 'Project Rejected'),
        ('PROJECT_CHANGES_REQUESTED', 'Project Changes Requested'),
        
        # INVESTMENT EVENTS (for investor)
        ('PAYMENT_SUCCESS', 'Payment Success'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('PAYMENT_PENDING', 'Payment Pending'),
        
        # ACCESS EVENTS (for investor/developer)
        ('ACCESS_APPROVED', 'Access Approved'),
        ('ACCESS_REJECTED', 'Access Rejected'),
        ('ACCESS_REQUESTED', 'Access Requested'),
        ('ACCESS_REVOKED', 'Access Revoked'),
        
        # GENERAL
        ('SYSTEM', 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.user.email}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    project_updates = models.BooleanField(default=True)
    investment_updates = models.BooleanField(default=True)
    access_updates = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"

