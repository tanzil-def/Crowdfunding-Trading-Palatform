import uuid
from django.db import models
from apps.users.models import User
from apps.projects.models import Project

class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('investor', 'project')
        ordering = ['-created_at']
