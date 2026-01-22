from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import AccessRequest

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Access Request Create Example',
            value={
                "project": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                "reason": "I am an institutional investor looking for detailed financial projections."
            }
        )
    ]
)
class AccessRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = ('id', 'project', 'reason', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Access Request List Example',
            value={
                "id": "b1a2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3",
                "project": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                "project_title": "Skyline Apartments",
                "status": "APPROVED",
                "reason": "Initial project evaluation",
                "created_at": "2026-01-20T14:00:00Z"
            }
        )
    ]
)
class AccessRequestListSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title')
    class Meta:
        model = AccessRequest
        fields = ('id', 'project', 'project_title', 'status', 'reason', 'created_at')

class AdminAccessRequestActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class AccessRequestActionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
