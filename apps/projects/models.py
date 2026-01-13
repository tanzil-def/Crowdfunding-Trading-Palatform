import uuid
import json
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings


class Project(models.Model):
    """Core Project model matching SRS requirements"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        NEEDS_CHANGES = 'NEEDS_CHANGES', 'Needs Changes'
        ARCHIVED = 'ARCHIVED', 'Archived'
        COMPLETED = 'COMPLETED', 'Completed'
    
    class Category(models.TextChoices):
        TECHNOLOGY = 'TECHNOLOGY', 'Technology'
        REAL_ESTATE = 'REAL_ESTATE', 'Real Estate'
        ENERGY = 'ENERGY', 'Energy'
        HEALTHCARE = 'HEALTHCARE', 'Healthcare'
        AGRICULTURE = 'AGRICULTURE', 'Agriculture'
        MANUFACTURING = 'MANUFACTURING', 'Manufacturing'
        RETAIL = 'RETAIL', 'Retail'
        SERVICES = 'SERVICES', 'Services'
        OTHER = 'OTHER', 'Other'
    
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    
    title = models.CharField(max_length=255, db_index=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER
    )
    
    
    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        db_index=True
    )
    
    
    total_project_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))] 
    )
    total_shares = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000000)]
    )
    shares_sold = models.PositiveIntegerField(default=0)
    
    
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    
    
    duration_days = models.PositiveIntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(365*2)]  
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    
    thumbnail = models.ImageField(
        upload_to='projects/thumbnails/',
        null=True,
        blank=True
    )
    
    
    model_3d = models.FileField(
        upload_to='projects/3d_models/',
        null=True,
        blank=True,
        help_text='Upload 3D model files (GLB, GLTF format)'
    )
    model_3d_size = models.PositiveIntegerField(default=0)  
    model_3d_format = models.CharField(max_length=20, blank=True)
    is_3d_public = models.BooleanField(default=False)
    
    
    financial_projections = models.TextField(blank=True)
    business_plan = models.TextField(blank=True)
    team_details = models.JSONField(default=dict, blank=True)
    legal_documents = models.URLField(blank=True)  
    risk_assessment = models.TextField(blank=True)
    

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_projects'
    )
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['developer', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        
        if self.total_shares == 0:
            raise ValidationError({'total_shares': 'Total shares must be greater than 0'})
        
    
        if self.duration_days < 30:
            raise ValidationError({'duration_days': 'Minimum project duration is 30 days'})
        
        
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date'})
    
    @property
    def per_share_price(self) -> Decimal:
        """Calculate price per share (SRS requirement)"""
        if self.total_shares > 0:
            return Decimal(self.total_project_value) / Decimal(self.total_shares)
        return Decimal('0.00')
    
    @property
    def remaining_shares(self) -> int:
        """Calculate remaining shares (SRS: Prevent overselling)"""
        return max(0, self.total_shares - self.shares_sold)
    
    @property
    def funding_progress(self) -> float:
        """Calculate funding progress percentage"""
        if self.total_shares > 0:
            return (self.shares_sold / self.total_shares) * 100
        return 0.0
    
    @property
    def funding_secured(self) -> Decimal:
        """Calculate total funding secured"""
        return Decimal(self.shares_sold) * self.per_share_price
    
    @property
    def is_fully_funded(self) -> bool:
        """Check if project is fully funded"""
        return self.shares_sold >= self.total_shares
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in project"""
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def can_edit(self, user) -> bool:
        """Check if user can edit project (SRS: Controlled edit rules)"""
        if user == self.developer:
            return self.status in [self.Status.DRAFT, self.Status.NEEDS_CHANGES]
        return False
    
    def can_submit(self, user) -> bool:
        """Check if user can submit project for review"""
        return user == self.developer and self.status == self.Status.DRAFT
    
    def update_shares(self, shares_to_sell: int):
        """Atomically update shares sold (SRS: Prevent overselling)"""
        if shares_to_sell < 0:
            raise ValueError("Cannot sell negative shares")
        
        if shares_to_sell > self.remaining_shares:
            raise ValueError(f"Not enough shares available. Requested: {shares_to_sell}, Available: {self.remaining_shares}")
        
        
        Project.objects.filter(id=self.id).update(
            shares_sold=models.F('shares_sold') + shares_to_sell
        )
        self.refresh_from_db()


class ProjectImage(models.Model):
    """Project images for gallery/carousel"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='projects/images/',
        height_field='image_height',
        width_field='image_width'
    )
    image_height = models.PositiveIntegerField(default=0)
    image_width = models.PositiveIntegerField(default=0)
    
    
    order = models.PositiveIntegerField(default=0)
    caption = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_images'
    )
    
    class Meta:
        db_table = 'project_images'
        ordering = ['order', 'uploaded_at']
        verbose_name = 'Project Image'
        verbose_name_plural = 'Project Images'
    
    def __str__(self):
        return f"Image for {self.project.title}"


class Favorite(models.Model):
    """User favorite projects (SRS: Favorites functionality)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        db_index=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        db_index=True
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'favorites'
        unique_together = ['user', 'project']
        ordering = ['-created_at']
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
    
    def __str__(self):
        return f"{self.user.email} favorited {self.project.title}"


class ProjectComparison(models.Model):
    """Project comparison (SRS: Compare 2-4 projects side by side)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comparisons',
        db_index=True
    )
    
    
    projects = models.ManyToManyField(
        Project,
        related_name='compared_in',
        limit_choices_to={'status': Project.Status.APPROVED}
    )
    
    
    name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_comparisons'
        ordering = ['-updated_at']
        verbose_name = 'Project Comparison'
        verbose_name_plural = 'Project Comparisons'
    
    def __str__(self):
        return f"Comparison by {self.user.email}"
    
    def clean(self):
        """Validate comparison constraints"""
        super().clean()
        
        
        if self.projects.count() < 2:
            raise ValidationError("Select at least 2 projects to compare")
        if self.projects.count() > 4:
            raise ValidationError("Cannot compare more than 4 projects")


class RestrictedAccessRequest(models.Model):
    """Request for access to restricted project data (SRS: Restricted access control)"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        REVOKED = 'REVOKED', 'Revoked'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='access_requests',
        limit_choices_to={'role': 'INVESTOR'}
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='access_requests'
    )
    
    # Request details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    purpose = models.TextField(blank=True)
    requested_fields = models.JSONField(default=list)  
    
    # Review information
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_access_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'restricted_access_requests'
        unique_together = ['investor', 'project']
        ordering = ['-created_at']
        verbose_name = 'Restricted Access Request'
        verbose_name_plural = 'Restricted Access Requests'
    
    def __str__(self):
        return f"{self.investor.email} → {self.project.title}"
    
    @property
    def has_access(self) -> bool:
        """Check if investor has access to restricted data"""
        return self.status == self.Status.APPROVED
    
    def approve(self, reviewer, notes: str = ''):
        """Approve access request"""
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def reject(self, reviewer, notes: str = ''):
        """Reject access request"""
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def revoke(self, reviewer, notes: str = ''):
        """Revoke access (SRS: Immediate revocation)"""
        self.status = self.Status.REVOKED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()


class ProjectAuditLog(models.Model):
    """Audit log for project actions (SRS: Audit trail)"""
    
    class ActionType(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
        ARCHIVED = 'ARCHIVED', 'Archived'
        RESTORED = 'RESTORED', 'Restored'
        FUNDING_UPDATED = 'FUNDING_UPDATED', 'Funding Updated'
        ACCESS_REQUESTED = 'ACCESS_REQUESTED', 'Access Requested'
        ACCESS_APPROVED = 'ACCESS_APPROVED', 'Access Approved'
        ACCESS_REVOKED = 'ACCESS_REVOKED', 'Access Revoked'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_actions'
    )
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    description = models.TextField(blank=True)
    
    
    changes = models.JSONField(default=dict, blank=True)
    
    
    metadata = models.JSONField(default=dict, blank=True)
    

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'project_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]
        verbose_name = 'Project Audit Log'
        verbose_name_plural = 'Project Audit Logs'
    
    def __str__(self):
        return f"{self.action_type} on {self.project.title}"


class ProjectStatistics(models.Model):
    """Project statistics for dashboard calculations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    
   
    total_investors = models.PositiveIntegerField(default=0)
    total_investments = models.PositiveIntegerField(default=0)
    average_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    
    daily_funding = models.JSONField(default=dict, blank=True)
    monthly_funding = models.JSONField(default=dict, blank=True)
    
   
    investor_countries = models.JSONField(default=dict, blank=True)
    investor_types = models.JSONField(default=dict, blank=True)
    
    
    funding_velocity = models.FloatField(default=0) 
    completion_rate = models.FloatField(default=0)  
    
    
    calculated_at = models.DateTimeField(auto_now=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    class Meta:
        db_table = 'project_statistics'
        verbose_name = 'Project Statistics'
        verbose_name_plural = 'Project Statistics'
    
    def __str__(self):
        return f"Statistics for {self.project.title}"