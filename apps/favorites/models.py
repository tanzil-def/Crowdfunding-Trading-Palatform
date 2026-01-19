import uuid
from django.db import models
from django.db.models import UniqueConstraint
from apps.users.models import User
from apps.projects.models import Project


class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            UniqueConstraint(
                fields=['investor', 'project'],
                name='unique_investor_project_favorite'
            )
        ]

    def __str__(self):
        return f"{self.investor} ❤️ {self.project}"
