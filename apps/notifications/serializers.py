from rest_framework import serializers
from .models import Notification
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Notification Example',
            value={
                "id": "c1f2a3b4-5678-4321-8765-432109876543",
                "type": "PROJECT_APPROVED",
                "message": "Your project 'Eco Solar' has been approved!",
                "is_read": False,
                "created_at": "2026-01-20T15:30:00Z"
            }
        )
    ]
)
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'type',
            'message',
            'is_read',
            'created_at'
        )
