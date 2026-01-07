from rest_framework import serializers
from .models import Project, ProjectMedia
from .services import calculate_share_price, validate_media

# ---------- Developer ----------
class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id','title','description','category',
            'total_project_value','total_shares',
            'restricted_fields','is_3d_restricted','created_at'
        )
        read_only_fields = ('id','created_at')

    def create(self, validated_data):
        validated_data['developer'] = self.context['request'].user
        validated_data['share_price'] = calculate_share_price(
            validated_data['total_project_value'],
            validated_data['total_shares']
        )
        return super().create(validated_data)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('title','description','category','restricted_fields','is_3d_restricted')


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id','title','category','status',
            'total_project_value','total_shares',
            'share_price','shares_sold','created_at'
        )


# ---------- Media ----------
class ProjectMediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMedia
        fields = ('id','type','file','is_restricted','uploaded_at')
        read_only_fields = ('id','uploaded_at')

    def validate(self, attrs):
        validate_media(attrs['file'], attrs['type'])
        return attrs


class ProjectMediaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMedia
        fields = ('id','type','file','is_restricted')


# ---------- Admin ----------
class AdminProjectListSerializer(serializers.ModelSerializer):
    developer_email = serializers.EmailField(source='developer.email')

    class Meta:
        model = Project
        fields = (
            'id','title','category','status',
            'developer_email','total_project_value',
            'total_shares','share_price','created_at'
        )
class InvestorProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'title',
            'category',
            'total_project_value',
            'total_shares',
            'share_price',
            'shares_sold',
            'created_at'
        )


class InvestorProjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'title',
            'description',
            'category',
o
            'total_project_value',
            'total_shares',
            'share_price',
            'shares_sold',
            'created_at'
        )

