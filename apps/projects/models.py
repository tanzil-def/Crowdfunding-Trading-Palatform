<<<<<<< HEAD
=======
# projects/models.py
import uuid
from django.db import models
from apps.users.models import User

class Project(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_CHANGES', 'Needs Changes'),
        ('ARCHIVED', 'Archived'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)

    total_project_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_shares = models.PositiveIntegerField(default=0)
    share_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shares_sold = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    restricted_fields = models.JSONField(default=dict, blank=True)
    is_3d_restricted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ProjectMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('MODEL_3D', '3D Model'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='IMAGE')  # <- default added
    file = models.FileField(upload_to='projects/')
    is_restricted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
>>>>>>> 83d38a9 (WIP: work in progress on project features)
