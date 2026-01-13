from rest_framework import serializers
from .models import Project, ProjectMedia
from .services import calculate_share_price, validate_media, filter_restricted_fields


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new projects by developers.
    """
    class Meta:
        model = Project
        fields = (
            "id", "title", "description", "category", "duration_days",
            "total_project_value", "total_shares",
            "restricted_fields", "is_3d_restricted", "created_at"
        )
        read_only_fields = ("id", "created_at")
    
    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["developer"] = user
        validated_data["share_price"] = calculate_share_price(
            validated_data["total_project_value"],
            validated_data["total_shares"]
        )
        return super().create(validated_data)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing projects.
    Only allows editing specific fields.
    """
    class Meta:
        model = Project
        fields = (
            "title", "description", "category", "duration_days",
            "restricted_fields", "is_3d_restricted"
        )


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing developer's projects.
    """
    remaining_shares = serializers.IntegerField(read_only=True)
    funding_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "status", "duration_days",
            "total_project_value", "total_shares", "share_price",
            "shares_sold", "remaining_shares", "funding_percentage",
            "created_at"
        )


class ProjectMediaUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading project media (images or 3D models).
    """
    class Meta:
        model = ProjectMedia
        fields = ("id", "type", "file", "is_restricted", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")
    
    def validate(self, attrs):
        media_type = attrs.get("type")
        file = attrs.get("file")
        
        if not media_type:
            raise serializers.ValidationError({"type": "Media type is required"})
        
        if file:
            validate_media(file, media_type)
        
        return attrs


class ProjectMediaListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing project media.
    """
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMedia
        fields = ("id", "type", "file", "file_url", "is_restricted", "uploaded_at")
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class AdminProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for admin project listing.
    """
    developer_email = serializers.EmailField(source="developer.email", read_only=True)
    developer_name = serializers.CharField(source="developer.get_full_name", read_only=True)
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "status", "duration_days",
            "developer_email", "developer_name",
            "total_project_value", "total_shares", "share_price",
            "created_at"
        )


class InvestorProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for investor project browsing/listing.
    """
    remaining_shares = serializers.IntegerField(read_only=True)
    funding_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "duration_days",
            "total_project_value", "total_shares", "share_price",
            "shares_sold", "remaining_shares", "funding_percentage",
            "created_at"
        )


class InvestorProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for investor project detail view.
    Handles restricted field filtering.
    """
    remaining_shares = serializers.IntegerField(read_only=True)
    funding_percentage = serializers.FloatField(read_only=True)
    has_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "description", "category", "duration_days",
            "total_project_value", "total_shares", "share_price",
            "shares_sold", "remaining_shares", "funding_percentage",
            "restricted_fields", "is_3d_restricted",
            "has_access", "created_at"
        )
    
    def get_has_access(self, obj):
        """
        Check if investor has approved access to restricted data.
        """
        user = self.context['request'].user
        
        if user.role == 'ADMIN' or user == obj.developer:
            return True
        
        if user.role == 'INVESTOR':
            from apps.access_requests.models import AccessRequest
            return AccessRequest.objects.filter(
                investor=user,
                project=obj,
                status='APPROVED'
            ).exists()
        
        return False
    
    def to_representation(self, instance):
        """
        Filter restricted fields based on user access.
        """
        data = super().to_representation(instance)
        user = self.context['request'].user
        
        if not data.get('has_access', False):
            data.pop('restricted_fields', None)
        
        return data