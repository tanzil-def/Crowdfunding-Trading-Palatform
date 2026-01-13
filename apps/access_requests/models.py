"""
Access Request Models - SRS 5.7 Compliant
Handles restricted data access control with audit trail
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AccessRequest(models.Model):
    """
    SRS: Verified investors can request access to restricted project data
    Admin can approve, reject, or revoke access with immediate effect
    All access decisions shall be logged
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Review')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        REVOKED = 'REVOKED', _('Revoked')

    # Core relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='access_requests',
        verbose_name=_('Investor'),
        help_text=_('Verified investor requesting access')
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='access_requests',
        verbose_name=_('Project')
    )

    # Request details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_('Status')
    )
    purpose = models.TextField(
        blank=True,
        verbose_name=_('Purpose'),
        help_text=_('Reason for requesting access')
    )
    requested_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Requested Fields'),
        help_text=_('Specific restricted fields requested (for audit)')
    )

    # Admin review info
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_access_requests',
        verbose_name=_('Reviewed By')
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'access_requests'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['investor', 'project'],
                condition=models.Q(status__in=['PENDING', 'APPROVED']),
                name='unique_active_access_request_per_investor_project'
            )
        ]
        indexes = [
            models.Index(fields=['investor', 'status']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['reviewed_at']),
        ]

    def __str__(self):
        return f"{self.investor.email} → {self.project.title} [{self.status}]"

    def clean(self):
        super().clean()

        if self.investor_id and hasattr(self.investor, 'is_verified'):
            if not self.investor.is_verified:
                raise ValidationError({
                    'investor': _('Only verified investors can request access')
                })

        if self.project_id and hasattr(self.project, 'status'):
            if self.project.status != 'APPROVED':
                raise ValidationError({
                    'project': _('Can only request access to approved projects')
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def has_active_access(self):
        return self.status == self.Status.APPROVED

    @property
    def is_reviewable(self):
        return self.status == self.Status.PENDING

    # ===== Business logic (BUG FIXED) =====

    def approve(self, reviewer, notes=''):
        if self.status != self.Status.PENDING:
            raise ValidationError(_('Only pending requests can be approved'))

        old_status = self.status

        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

        self._create_history_entry(
            old_status,
            self.Status.APPROVED,
            reviewer,
            notes
        )

    def reject(self, reviewer, notes=''):
        if self.status != self.Status.PENDING:
            raise ValidationError(_('Only pending requests can be rejected'))

        old_status = self.status

        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

        self._create_history_entry(
            old_status,
            self.Status.REJECTED,
            reviewer,
            notes
        )

    def revoke(self, reviewer, notes=''):
        if self.status != self.Status.APPROVED:
            raise ValidationError(_('Only approved access can be revoked'))

        old_status = self.status

        self.status = self.Status.REVOKED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

        self._create_history_entry(
            old_status,
            self.Status.REVOKED,
            reviewer,
            notes
        )

    def _create_history_entry(self, previous_status, new_status, reviewer, notes):
        AccessRequestHistory.objects.create(
            access_request=self,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=reviewer,
            notes=notes
        )


class AccessRequestHistory(models.Model):
    """
    SRS: Audit trail for all access decisions
    Immutable log of status changes
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access_request = models.ForeignKey(
        AccessRequest,
        on_delete=models.CASCADE,
        related_name='history_entries'
    )

    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'access_request_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['access_request', 'changed_at']),
        ]

    def __str__(self):
        return f"{self.access_request.id}: {self.previous_status}→{self.new_status}"
