from rest_framework import serializers
from .models import Project, ProjectMedia

# ------------------ Project Serializers ------------------

class ProjectListSerializer(serializers.ModelSerializer):
    per_share_price = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'category', 'status', 'total_project_value',
            'total_shares', 'per_share_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['per_share_price']

    def get_per_share_price(self, obj):
        return obj.per_share_price


class ProjectDetailSerializer(serializers.ModelSerializer):
    per_share_price = serializers.SerializerMethodField()
    developer_email = serializers.ReadOnlyField(source='developer.email')

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'category',
            'duration',
            'total_project_value',
            'total_shares',
            'status',
            'is_archived',
            'created_at',
            'updated_at',
            'per_share_price',
            'developer_email',
        ]
        read_only_fields = [
            'status',
            'is_archived',
            'created_at',
            'updated_at',
            'per_share_price',
            'developer_email',
        ]
        extra_kwargs = {
            'total_project_value': {
                'min_value': 1.00,
                'decimal_places': 2,
            },
            'total_shares': {
                'min_value': 1,
                'max_value': 1000000,  # realistic upper limit
            },
        }

    def get_per_share_price(self, obj):
        return obj.per_share_price


# ------------------ Project Media Serializers ------------------

class ProjectMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectMedia
        fields = [
            'id', 'media_type', 'file_url', 'file_size_mb',
            'is_restricted', 'uploaded_at'
        ]
        read_only_fields = ['file_url', 'file_size_mb', 'uploaded_at']

    def get_file_url(self, obj):
        if obj.file and not getattr(obj, 'is_deleted', False):
            return obj.file.url
        return None

    def get_file_size_mb(self, obj):
        if obj.file:
            return round(obj.file.size / (1024 * 1024), 2)
        return 0


class ProjectMediaCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = ProjectMedia
        fields = ['file', 'media_type', 'is_restricted']

    def validate(self, data):
        file = data.get('file')
        name = file.name.lower() if file else ''

        # Auto-detect media_type if not provided
        if 'media_type' not in data or not data['media_type']:
            if name.endswith(('.glb', '.gltf')):
                data['media_type'] = 'MODEL_3D'
            elif name.endswith(('.mp4', '.webm', '.mov')):
                data['media_type'] = 'VIDEO'
            else:
                data['media_type'] = 'IMAGE'
        return data
