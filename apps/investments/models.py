import uuid
from django.db import models
from apps.users.models import User
from apps.projects.models import Project

class PaymentTransaction(models.Model):

    STATUS_CHOICES = (
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(max_length=255, unique=True)  # gateway reference
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    raw_payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SharePurchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_purchases')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='share_purchases')
    shares_purchased = models.PositiveIntegerField()
    price_per_share = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='share_purchase')
    created_at = models.DateTimeField(auto_now_add=True)
