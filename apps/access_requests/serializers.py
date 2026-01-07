from rest_framework import serializers
from .models import AccessRequest

class AccessRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = ('id', 'project', 'reason', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

class AccessRequestListSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title')
    class Meta:
        model = AccessRequest
        fields = ('id', 'project', 'project_title', 'status', 'reason', 'created_at')

class AdminAccessRequestActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
