from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer, OpenApiExample
from decimal import Decimal, ROUND_HALF_UP
from django.core.validators import MinValueValidator
from .models import Project, ProjectMedia
from .services import calculate_share_price, validate_media, filter_restricted_fields


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Project Creation Example',
            value={
                "title": "Green Energy Park",
                "description": "Large scale solar farm project",
                "category": "Sustainability",
                "duration_days": 365,
                "total_project_value": "1000000.00",
                "total_shares": 10000,
                "restricted_fields": ["financial_report", "blueprints"],
                "is_3d_restricted": True
            }
        )
    ]
)
class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new projects by developers.
    """
    total_project_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Total value of the project (e.g. 1000000.00)"
    )
    total_shares = serializers.IntegerField(min_value=1, help_text="Total share count (e.g. 1000)")
    restricted_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="List of restricted field keys"
    )

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
        
        # Ensure share_price calculation is precise and rounded
        price = calculate_share_price(
            validated_data["total_project_value"],
            validated_data["total_shares"]
        )
        validated_data["share_price"] = price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return super().create(validated_data)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Project Update Example',
            value={
                "title": "Green Energy Park v2",
                "description": "Updated solar farm project",
                "category": "Sustainability",
                "duration_days": 400,
                "restricted_fields": ["financial_report"],
                "is_3d_restricted": False
            }
        )
    ]
)
class ProjectUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing projects.
    Only allows editing specific fields.
    """
    restricted_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of restricted field keys"
    )

    class Meta:
        model = Project
        fields = (
            "title", "description", "category", "duration_days",
            "restricted_fields", "is_3d_restricted"
        )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Developer Project List Example',
            value={
                "id": "a1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3",
                "title": "Solar Field Alpha",
                "category": "Energy",
                "status": "APPROVED",
                "duration_days": 365,
                "total_project_value": "750000.00",
                "total_shares": 750,
                "share_price": "1000.00",
                "shares_sold": 500,
                "remaining_shares": 250,
                "funding_percentage": 66.67,
                "created_at": "2026-01-20T08:00:00Z"
            }
        )
    ]
)
class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing developer's projects.
    """
    remaining_shares = serializers.IntegerField(read_only=True, min_value=0, help_text="Remaining shares (e.g. 250)")
    funding_percentage = serializers.FloatField(read_only=True, min_value=0.0, help_text="Funding percentage (e.g. 75.0)")

    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "status", "duration_days",
            "total_project_value", "total_shares", "share_price",
            "shares_sold", "remaining_shares", "funding_percentage",
            "created_at"
        )
        read_only_fields = ("id", "created_at", "total_project_value", "share_price", "shares_sold")
    
    # Explicit field definitions to enforce OAS examples on model fields
    total_project_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Total project value (e.g. 750000.00)")
    share_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Price per share (e.g. 1500.00)")
    shares_sold = serializers.IntegerField(min_value=0, read_only=True, help_text="Shares sold (e.g. 500)")


class ProjectMediaUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading project media (images or 3D models).
    """
    file = serializers.FileField(help_text="The binary file to upload (e.g., .jpg, .png, .mp4, .glb)")

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


class ProjectMediaRequestSerializer(serializers.Serializer):
    """
    Dedicated serializer for media upload requests to ensure correct Swagger detection.
    """
    type = serializers.ChoiceField(
        choices=ProjectMedia.MEDIA_TYPE_CHOICES,
        help_text="Type of media (IMAGE, VIDEO, or 3D MODEL)"
    )
    file = serializers.FileField(help_text="Binary file to upload")
    is_restricted = serializers.BooleanField(default=False, help_text="Restrict access to this asset")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Project Media List Example',
            value={
                "id": "e5f6a7b8-c9d0-4e1f-a2b3-c4d5e6f7a8b9",
                "type": "MODEL",
                "file": "https://cdn.example.com/media/solar_model.glb",
                "file_url": "https://cdn.example.com/media/solar_model.glb",
                "file_extension": "glb",
                "is_restricted": True,
                "uploaded_at": "2026-01-20T12:00:00Z"
            }
        )
    ]
)
class ProjectMediaListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing project media.
    """
    file_url = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMedia
        fields = ("id", "type", "file", "file_url", "file_extension", "is_restricted", "uploaded_at")
    
    @extend_schema_field(serializers.CharField(help_text="File extension (e.g. 'glb', 'jpg'). Frontend 3D viewer uses this to load appropriate renderer."))
    def get_file_extension(self, obj):
        if not obj.file:
            return None
        return obj.file.name.split('.')[-1].lower()
    
    @extend_schema_field(serializers.URLField())
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Admin Project List Example',
            value={
                "id": "d1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3",
                "title": "Wind Farm Beta",
                "category": "Energy",
                "status": "PENDING",
                "duration_days": 180,
                "developer_email": "d***r@example.com",
                "developer_name": "John Doe",
                "total_project_value": "2500000.00",
                "total_shares": 2500,
                "share_price": "1000.00",
                "created_at": "2026-01-20T09:00:00Z"
            }
        )
    ]
)
class AdminProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for admin project listing.
    """
    developer_email = serializers.EmailField(source="developer.email", read_only=True, help_text="Developer email (masked, e.g. d***r@example.com)")
    developer_name = serializers.CharField(source="developer.get_full_name", read_only=True)
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "status", "duration_days",
            "developer_email", "developer_name",
            "total_project_value", "total_shares", "share_price",
            "created_at"
        )
    
    total_project_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Total value (e.g. 1200000.00)")
    total_shares = serializers.IntegerField(min_value=1, read_only=True, help_text="Total shares (e.g. 1200)")
    share_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Share price (e.g. 1000.00)")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Investor Project Example',
            value={
                "id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                "title": "Skyline Apartments",
                "category": "Real Estate",
                "duration_days": 730,
                "total_project_value": "5000000.00",
                "total_shares": 5000,
                "share_price": "1000.00",
                "shares_sold": 1500,
                "remaining_shares": 3500,
                "funding_percentage": 30.0,
                "created_at": "2026-01-20T10:00:00Z"
            }
        )
    ]
)
class InvestorProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for investor project browsing/listing.
    """
    remaining_shares = serializers.IntegerField(read_only=True, min_value=0, help_text="Remaining shares (e.g. 400)")
    funding_percentage = serializers.FloatField(read_only=True, min_value=0.0, help_text="Funding percentage (e.g. 66.67)")
    
    class Meta:
        model = Project
        fields = (
            "id", "title", "category", "duration_days",
            "total_project_value", "total_shares", "share_price",
            "shares_sold", "remaining_shares", "funding_percentage",
            "created_at"
        )
    
    total_project_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Total project value (e.g. 500000.00)")
    total_shares = serializers.IntegerField(min_value=1, read_only=True, help_text="Total shares (e.g. 5000)")
    share_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Share price (e.g. 100.00)")
    shares_sold = serializers.IntegerField(min_value=0, read_only=True, help_text="Shares sold (e.g. 1500)")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Investor Project Detail Example',
            value={
                "id": "f1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3",
                "title": "Tech Hub Construction",
                "description": "Building a modern technology center",
                "category": "Real Estate",
                "duration_days": 540,
                "total_project_value": "10000000.00",
                "total_shares": 10000,
                "share_price": "1000.00",
                "shares_sold": 8500,
                "remaining_shares": 1500,
                "funding_percentage": 85.0,
                "restricted_fields": ["architectural_plans", "budget_breakdown"],
                "is_3d_restricted": True,
                "has_access": True,
                "created_at": "2026-01-15T14:30:00Z"
            }
        )
    ]
)
class InvestorProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for investor project detail view.
    Handles restricted field filtering.
    """
    remaining_shares = serializers.IntegerField(read_only=True, min_value=0, help_text="Remaining shares (e.g. 100)")
    funding_percentage = serializers.FloatField(read_only=True, min_value=0.0, help_text="Funding percentage (e.g. 90.0)")
    restricted_fields = serializers.ListField(
        child=serializers.CharField(),
        read_only=True, 
        help_text="List of restricted field keys"
    )
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
    
    total_project_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Total project value (e.g. 850000.00)")
    total_shares = serializers.IntegerField(min_value=1, read_only=True, help_text="Total shares (e.g. 850)")
    share_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), read_only=True, help_text="Share price (e.g. 1000.00)")
    shares_sold = serializers.IntegerField(min_value=0, read_only=True, help_text="Shares sold (e.g. 425)")
    
    @extend_schema_field(serializers.BooleanField())
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



class ProjectActionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class ProjectRejectRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, help_text="Reason for rejection")


class ProjectChangesRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, help_text="Note for developer")


class ProjectComparisonSerializer(serializers.ModelSerializer):
    """
    Serializer for comparator feature - displays projects side by side.
    Respects restricted field access control.
    """
    remaining_shares = serializers.IntegerField(read_only=True, help_text="Remaining shares available")
    funding_percentage = serializers.FloatField(read_only=True, help_text="Funding percentage (0-100)")
    has_access = serializers.SerializerMethodField(help_text="Whether user has access to restricted fields")
    developer_name = serializers.CharField(source='developer.get_full_name', read_only=True)
    
    class Meta:
        model = Project
        fields = (
            'id', 'title', 'description', 'category', 'duration_days',
            'total_project_value', 'total_shares', 'share_price',
            'shares_sold', 'remaining_shares', 'funding_percentage',
            'developer_name', 'restricted_fields', 'is_3d_restricted',
            'has_access', 'created_at'
        )
    
    @extend_schema_field(serializers.BooleanField())
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
        has_access = data.get('has_access', False)
        
        # If user doesn't have access, hide restricted fields
        if not has_access and instance.restricted_fields:
            for field in instance.restricted_fields or []:
                data[field] = None
        
        return data


class ProjectComparatorRequestSerializer(serializers.Serializer):
    """
    Request serializer for comparator endpoint.
    Validates project IDs (2-4 projects required).
    """
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        max_length=4,
        help_text="List of 2-4 project UUIDs to compare"
    )
    
    def validate_project_ids(self, value):
        """Ensure projects exist and are approved"""
        from .models import Project
        
        projects = Project.objects.filter(id__in=value, status='APPROVED')
        
        if projects.count() != len(value):
            raise serializers.ValidationError(
                f"Some projects don't exist or aren't approved. Found {projects.count()} of {len(value)}."
            )
        
        return value


class ProjectComparatorResponseSerializer(serializers.Serializer):
    """
    Response serializer for comparator feature.
    Contains projects with access control applied.
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(
        child=serializers.ListField(child=ProjectComparisonSerializer()),
        help_text="Comparison data with 'projects' key containing project list"
    )
    restricted_fields = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of fields that require approved access to view"
    )