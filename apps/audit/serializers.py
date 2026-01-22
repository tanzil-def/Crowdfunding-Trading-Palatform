from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import AuditLog

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Audit Log Example',
            value={
                "id": "e1f2a3b4-c5d6-4e5f-a6b7-c8d9e0f1a2b3",
                "actor_email": "admin@example.com",
                "action": "PROJECT_APPROVED",
                "entity_type": "PROJECT",
                "entity_id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                "metadata": {"approved_at": "2026-01-20T10:00:00Z"},
                "created_at": "2026-01-20T10:00:00Z"
            }
        )
    ]
)
class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            'id',
            'actor_email',
            'action',
            'entity_type',
            'entity_id',
            'metadata',
            'created_at'
        )
        read_only_fields = fields  # Fully read-only
