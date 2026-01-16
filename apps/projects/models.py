import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
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
    duration_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Project duration in days"
    )
    
    total_project_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_shares = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    share_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    shares_sold = models.PositiveIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    restricted_fields = models.JSONField(default=dict, blank=True)
    is_3d_restricted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['developer', 'status']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
    @property
    def remaining_shares(self):
        return self.total_shares - self.shares_sold
    
    @property
    def funding_percentage(self):
        if self.total_shares == 0:
            return 0
        return (self.shares_sold / self.total_shares) * 100


class ProjectMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('MODEL_3D', '3D Model'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to='projects/%Y/%m/')
    is_restricted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['project', 'type']),
        ]
    
    def __str__(self):
        return f"{self.project.title} - {self.type}"