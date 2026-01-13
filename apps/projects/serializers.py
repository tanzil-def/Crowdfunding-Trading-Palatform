from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import (
    Project, ProjectImage, Favorite, 
    ProjectComparison, RestrictedAccessRequest
)
from apps.users.serializers import UserSerializer


class ProjectImageSerializer(serializers.ModelSerializer):
    """Serializer for project images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectImage
        fields = [
            'id', 'image_url', 'caption', 'order',
            'is_featured', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project listing (public view)"""
    
    developer = UserSerializer(read_only=True)
    per_share_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        read_only=True
    )
    remaining_shares = serializers.IntegerField(read_only=True)
    funding_progress = serializers.FloatField(read_only=True)
    funding_secured = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    thumbnail_url = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'short_description', 'category',
            'developer', 'status', 'created_at',
            'total_project_value', 'total_shares', 'shares_sold',
            'per_share_price', 'remaining_shares',
            'funding_progress', 'funding_secured',
            'duration_days', 'start_date', 'end_date',
            'thumbnail_url', 'is_favorited', 'tags'
        ]
        read_only_fields = fields
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for project detail view"""
    
    developer = UserSerializer(read_only=True)
    images = ProjectImageSerializer(many=True, read_only=True)
    
    # Financial metrics
    per_share_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        read_only=True
    )
    remaining_shares = serializers.IntegerField(read_only=True)
    funding_progress = serializers.FloatField(read_only=True)
    funding_secured = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    days_remaining = serializers.IntegerField(read_only=True)
    
    # Media URLs
    thumbnail_url = serializers.SerializerMethodField()
    model_3d_url = serializers.SerializerMethodField()
    
    # Restricted fields (conditional)
    restricted_data = serializers.SerializerMethodField()
    has_restricted_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'short_description', 'description', 'category',
            'developer', 'status', 'created_at', 'updated_at',
            
            # Financial
            'total_project_value', 'total_shares', 'shares_sold',
            'per_share_price', 'remaining_shares',
            'funding_progress', 'funding_secured',
            
            # Timeline
            'duration_days', 'start_date', 'end_date', 'days_remaining',
            
            # Media
            'thumbnail_url', 'images', 'model_3d_url', 'is_3d_public',
            
            # Restricted data
            'restricted_data', 'has_restricted_access',
            
            # Metadata
            'tags', 'review_notes'
        ]
        read_only_fields = fields
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_model_3d_url(self, obj):
        request = self.context.get('request')
        if obj.model_3d and request and (obj.is_3d_public or self.has_restricted_access(obj)):
            return request.build_absolute_uri(obj.model_3d.url)
        return None
    
    def get_has_restricted_access(self, obj):
        """Check if current user has access to restricted data"""
        request = self.context.get('request')
        user = request.user if request else None
        
        if not user or not user.is_authenticated:
            return False
        
        # Admins and developers have full access
        if user.is_admin or user == obj.developer:
            return True
        
        # Check if investor has approved access request
        if user.is_investor:
            return RestrictedAccessRequest.objects.filter(
                investor=user,
                project=obj,
                status=RestrictedAccessRequest.Status.APPROVED
            ).exists()
        
        return False
    
    def get_restricted_data(self, obj):
        """Return restricted data only if user has access"""
        if not self.get_has_restricted_access(obj):
            return {}
        
        return {
            'financial_projections': obj.financial_projections,
            'business_plan': obj.business_plan,
            'team_details': obj.team_details,
            'legal_documents': obj.legal_documents,
            'risk_assessment': obj.risk_assessment,
        }


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects (Developers only)"""
    
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Project
        fields = [
            'title', 'short_description', 'description', 'category',
            'total_project_value', 'total_shares', 'duration_days',
            'financial_projections', 'business_plan', 'team_details',
            'legal_documents', 'risk_assessment', 'tags',
            'thumbnail', 'images'
        ]
    
    def validate(self, attrs):
        # Ensure total shares is positive
        if attrs.get('total_shares', 0) <= 0:
            raise serializers.ValidationError({
                'total_shares': 'Total shares must be greater than 0'
            })
        
        # Ensure total value is positive
        if attrs.get('total_project_value', 0) <= 0:
            raise serializers.ValidationError({
                'total_project_value': 'Total project value must be greater than 0'
            })
        
        # Calculate and validate per share price
        if attrs.get('total_project_value') and attrs.get('total_shares'):
            per_share = attrs['total_project_value'] / attrs['total_shares']
            if per_share < Decimal('0.01'):
                raise serializers.ValidationError({
                    'total_shares': 'Per share price must be at least $0.01'
                })
        
        return attrs
    
    def create(self, validated_data):
        images = validated_data.pop('images', [])
        
        # Set developer from request context
        validated_data['developer'] = self.context['request'].user
        
        # Create project
        project = Project.objects.create(**validated_data)
        
        # Create project images
        for index, image in enumerate(images):
            ProjectImage.objects.create(
                project=project,
                image=image,
                order=index,
                uploaded_by=self.context['request'].user
            )
        
        # Create audit log entry
        from .services import create_audit_log
        create_audit_log(
            project=project,
            actor=self.context['request'].user,
            action_type='CREATED',
            description=f"Project '{project.title}' created"
        )
        
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects"""
    
    class Meta:
        model = Project
        fields = [
            'title', 'short_description', 'description', 'category',
            'duration_days', 'financial_projections', 'business_plan',
            'team_details', 'legal_documents', 'risk_assessment',
            'tags', 'thumbnail'
        ]
    
    def validate(self, attrs):
        instance = self.instance
        
        # Validate edit permissions based on status
        if instance.status not in [Project.Status.DRAFT, Project.Status.NEEDS_CHANGES]:
            raise serializers.ValidationError(
                "Project can only be edited in DRAFT or NEEDS_CHANGES status"
            )
        
        return attrs
    
    def update(self, instance, validated_data):
        # Track changes for audit log
        changes = {}
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value) if old_value else None,
                    'new': str(new_value) if new_value else None
                }
        
        # Update instance
        instance = super().update(instance, validated_data)
        
        # Create audit log if changes were made
        if changes:
            from .services import create_audit_log
            create_audit_log(
                project=instance,
                actor=self.context['request'].user,
                action_type='UPDATED',
                description=f"Project '{instance.title}' updated",
                changes=changes
            )
        
        return instance


class ProjectSubmitSerializer(serializers.Serializer):
    """Serializer for submitting project for review"""
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        instance = self.instance
        
        # Ensure project is in draft status
        if instance.status != Project.Status.DRAFT:
            raise serializers.ValidationError(
                "Only draft projects can be submitted for review"
            )
        
        # Validate required fields are filled
        required_fields = [
            'title', 'short_description', 'description', 'category',
            'total_project_value', 'total_shares', 'duration_days'
        ]
        
        for field in required_fields:
            value = getattr(instance, field)
            if not value:
                raise serializers.ValidationError(
                    f"Field '{field}' is required before submission"
                )
        
        return attrs
    
    def save(self, **kwargs):
        instance = self.instance
        instance.status = Project.Status.PENDING_REVIEW
        instance.submitted_at = timezone.now()
        instance.save()
        
        # Create audit log
        from .services import create_audit_log
        create_audit_log(
            project=instance,
            actor=self.context['request'].user,
            action_type='SUBMITTED',
            description=f"Project '{instance.title}' submitted for review"
        )
        
        return instance


class ProjectReviewSerializer(serializers.Serializer):
    """Serializer for admin project review"""
    
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'request_changes']
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        instance = self.instance
        
        # Ensure project is pending review
        if instance.status != Project.Status.PENDING_REVIEW:
            raise serializers.ValidationError(
                "Project is not in pending review status"
            )
        
        return attrs
    
    def save(self, **kwargs):
        instance = self.instance
        action = self.validated_data['action']
        notes = self.validated_data.get('notes', '')
        
        if action == 'approve':
            instance.status = Project.Status.APPROVED
            instance.start_date = timezone.now()
            if instance.duration_days:
                instance.end_date = instance.start_date + timezone.timedelta(days=instance.duration_days)
            action_type = 'APPROVED'
            description = f"Project '{instance.title}' approved"
        
        elif action == 'reject':
            instance.status = Project.Status.REJECTED
            action_type = 'REJECTED'
            description = f"Project '{instance.title}' rejected"
        
        elif action == 'request_changes':
            instance.status = Project.Status.NEEDS_CHANGES
            action_type = 'CHANGES_REQUESTED'
            description = f"Changes requested for project '{instance.title}'"
        
        instance.reviewed_at = timezone.now()
        instance.reviewed_by = self.context['request'].user
        instance.review_notes = notes
        instance.save()
        
        # Create audit log
        from .services import create_audit_log
        create_audit_log(
            project=instance,
            actor=self.context['request'].user,
            action_type=action_type,
            description=description,
            metadata={'review_notes': notes}
        )
        
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites"""
    
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'project', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating favorites"""
    
    class Meta:
        model = Favorite
        fields = ['project', 'notes']
    
    def validate(self, attrs):
        project = attrs.get('project')
        user = self.context['request'].user
        
        # Ensure project is approved
        if project.status != Project.Status.APPROVED:
            raise serializers.ValidationError({
                'project': 'Only approved projects can be favorited'
            })
        
        # Check if already favorited
        if Favorite.objects.filter(user=user, project=project).exists():
            raise serializers.ValidationError({
                'project': 'Project is already in favorites'
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProjectComparisonSerializer(serializers.ModelSerializer):
    """Serializer for project comparisons"""
    
    projects = ProjectListSerializer(many=True, read_only=True)
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = ProjectComparison
        fields = [
            'id', 'name', 'notes', 'projects', 'project_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'projects']
    
    def validate_project_ids(self, value):
        # SRS: Compare 2 to 4 projects
        if len(value) < 2:
            raise serializers.ValidationError("Select at least 2 projects to compare")
        if len(value) > 4:
            raise serializers.ValidationError("Cannot compare more than 4 projects")
        
        # Validate projects exist and are approved
        projects = Project.objects.filter(id__in=value, status=Project.Status.APPROVED)
        if projects.count() != len(value):
            raise serializers.ValidationError("Some projects are not available for comparison")
        
        return value
    
    def create(self, validated_data):
        project_ids = validated_data.pop('project_ids')
        validated_data['user'] = self.context['request'].user
        
        comparison = ProjectComparison.objects.create(**validated_data)
        comparison.projects.set(project_ids)
        
        return comparison
    
    def update(self, instance, validated_data):
        project_ids = validated_data.pop('project_ids', None)
        
        instance = super().update(instance, validated_data)
        
        if project_ids is not None:
            instance.projects.set(project_ids)
        
        return instance


class RestrictedAccessRequestSerializer(serializers.ModelSerializer):
    """Serializer for restricted access requests"""
    
    investor = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    project_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = RestrictedAccessRequest
        fields = [
            'id', 'investor', 'project', 'project_id',
            'status', 'purpose', 'requested_fields',
            'review_notes', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'investor', 'project', 'status',
            'review_notes', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        project_id = attrs.get('project_id')
        user = self.context['request'].user
        
        # Ensure user is an investor
        if not user.is_investor:
            raise serializers.ValidationError({
                'detail': 'Only investors can request access to restricted data'
            })
        
        # Ensure project exists and is approved
        try:
            project = Project.objects.get(id=project_id, status=Project.Status.APPROVED)
        except Project.DoesNotExist:
            raise serializers.ValidationError({
                'project_id': 'Project not found or not approved'
            })
        
        # Check for existing request
        if RestrictedAccessRequest.objects.filter(
            investor=user, 
            project=project
        ).exists():
            raise serializers.ValidationError({
                'detail': 'You have already requested access to this project'
            })
        
        attrs['project'] = project
        return attrs
    
    def create(self, validated_data):
        validated_data['investor'] = self.context['request'].user
        return super().create(validated_data)


class RestrictedAccessReviewSerializer(serializers.Serializer):
    """Serializer for reviewing access requests"""
    
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'revoke']
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def save(self, **kwargs):
        instance = self.instance
        action = self.validated_data['action']
        notes = self.validated_data.get('notes', '')
        
        if action == 'approve':
            instance.approve(self.context['request'].user, notes)
        elif action == 'reject':
            instance.reject(self.context['request'].user, notes)
        elif action == 'revoke':
            instance.revoke(self.context['request'].user, notes)
        
        return instance


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics"""
    
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    total_funding_secured = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_investors = serializers.IntegerField()
    average_funding_rate = serializers.FloatField()
    
    # Time-based metrics
    today_funding = serializers.DecimalField(max_digits=15, decimal_places=2)
    weekly_funding = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_funding = serializers.DecimalField(max_digits=15, decimal_places=2)