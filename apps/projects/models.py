from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.users.models import CustomUser

# ---------------------- Project Model ----------------------
class Project(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_CHANGES', 'Needs Changes'),
        ('ARCHIVED', 'Archived'),
    )

    developer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)  # e.g., Tech, Art, Health
    duration = models.DurationField(help_text="Project duration, e.g., 90 days")
    total_project_value = models.DecimalField(max_digits=16, decimal_places=2)
    total_shares = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_archived = models.BooleanField(default=False)  # soft archive

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.developer.email}"

    # ---------------- Computed Property ----------------
    @property
    def per_share_price(self):
        if self.total_shares > 0:
            return round(self.total_project_value / self.total_shares, 2)
        return 0

    # ---------------- Validation ----------------
    def clean(self):
        if self.total_shares <= 0:
            raise ValidationError("Total shares must be greater than 0.")
        if self.total_project_value <= 0:
            raise ValidationError("Total project value must be greater than 0.")

    # ---------------- Save Override ----------------
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ---------------------- Project Media Model ----------------------
class ProjectMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('MODEL_3D', '3D Model'),
        ('VIDEO', 'Short Video'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='projects/media/%Y/%m/%d/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    is_restricted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)  # soft delete

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        status = 'Restricted' if self.is_restricted else 'Public'
        return f"{self.media_type} - {self.project.title} ({status})"

    # ---------------- Validation ----------------
    def clean(self):
        if not self.file:
            return

        # File size limit from settings or default 50MB
        max_size_mb = getattr(settings, 'PROJECT_MEDIA_MAX_SIZE_MB', 50)
        if self.file.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"File size must be under {max_size_mb}MB.")

        # Format validation
        name = self.file.name.lower()
        if self.media_type == 'IMAGE':
            if not name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                raise ValidationError("Invalid image format. Allowed: JPG, PNG, WebP, GIF.")
        elif self.media_type == 'MODEL_3D':
            if not name.endswith(('.glb', '.gltf')):
                raise ValidationError("Invalid 3D format. Allowed: GLB, GLTF only.")
        elif self.media_type == 'VIDEO':
            if not name.endswith(('.mp4', '.webm', '.mov')):
                raise ValidationError("Invalid video format. Allowed: MP4, WebM, MOV.")

    # ---------------- Save Override ----------------
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
