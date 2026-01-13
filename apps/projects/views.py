from django.db.models import Q, F, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import (
    Project, ProjectImage, Favorite, 
    ProjectComparison, RestrictedAccessRequest
)
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, ProjectUpdateSerializer,
    ProjectSubmitSerializer, ProjectReviewSerializer,
    FavoriteSerializer, FavoriteCreateSerializer,
    ProjectComparisonSerializer, RestrictedAccessRequestSerializer,
    RestrictedAccessReviewSerializer, ProjectStatsSerializer
)
from .services import (
    create_project, submit_project_for_review, review_project,
    add_to_favorites, create_project_comparison,
    request_restricted_access, review_access_request,
    get_developer_dashboard_data, get_investor_dashboard_data,
    validate_media_file
)
from apps.users.permissions import (
    IsAdminUser, IsDeveloperUser, IsInvestorUser,
    IsVerifiedUser, CanInvest
)
from utils.pagination import StandardResultsSetPagination
from utils.filters import ProjectFilter


# ==================== PROJECT VIEWS ====================

class ProjectListView(generics.ListAPIView):
    """
    List all approved projects (public)
    
    SRS: Investors browse approved projects with search and filtering
    """
    serializer_class = ProjectListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ['title', 'short_description', 'description', 'category']
    ordering_fields = ['created_at', 'total_project_value', 'funding_progress']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return approved projects only
        Admin can see all, developers see their own + approved, investors see approved
        """
        queryset = Project.objects.filter(status=Project.Status.APPROVED)
        
        # Apply additional filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        min_progress = self.request.query_params.get('min_progress')
        if min_progress:
            queryset = queryset.annotate(
                funding_progress_calc=(F('shares_sold') * 100.0) / F('total_shares')
            ).filter(funding_progress_calc__gte=float(min_progress))
        
        max_progress = self.request.query_params.get('max_progress')
        if max_progress:
            queryset = queryset.annotate(
                funding_progress_calc=(F('shares_sold') * 100.0) / F('total_shares')
            ).filter(funding_progress_calc__lte=float(max_progress))
        
        return queryset.select_related('developer').prefetch_related('images')


class ProjectDetailView(generics.RetrieveAPIView):
    """
    Get project details
    
    SRS: Show project details with restricted fields conditionally
    """
    serializer_class = ProjectDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    queryset = Project.objects.all()
    
    def get_queryset(self):
        """Return queryset based on user permissions"""
        queryset = Project.objects.all()
        
        # Non-authenticated users can only see approved projects
        if not self.request.user.is_authenticated:
            return queryset.filter(status=Project.Status.APPROVED)
        
        # Authenticated users: investors see approved, developers see their own + approved
        if self.request.user.is_investor:
            return queryset.filter(status=Project.Status.APPROVED)
        
        return queryset.filter(
            Q(status=Project.Status.APPROVED) |
            Q(developer=self.request.user)
        ).distinct()


class ProjectCreateView(generics.CreateAPIView):
    """
    Create a new project (Developers only)
    
    SRS: Developers create projects
    """
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    
    def perform_create(self, serializer):
        """Create project with developer from request"""
        serializer.save(developer=self.request.user)
        
        # Log the creation
        from .services import create_audit_log
        create_audit_log(
            project=serializer.instance,
            actor=self.request.user,
            action_type='CREATED',
            description=f"Project '{serializer.instance.title}' created",
            request=self.request
        )


class ProjectUpdateView(generics.UpdateAPIView):
    """
    Update project (Developers only, only in draft/needs_changes)
    
    SRS: Controlled edit rules based on project status
    """
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Only allow developers to edit their own projects"""
        return Project.objects.filter(developer=self.request.user)
    
    def get_object(self):
        """Get project and validate edit permissions"""
        project = super().get_object()
        
        # Check if project can be edited
        if not project.can_edit(self.request.user):
            raise PermissionDenied(
                "Project can only be edited in DRAFT or NEEDS_CHANGES status"
            )
        
        return project


class ProjectSubmitView(generics.GenericAPIView):
    """
    Submit project for admin review
    
    SRS: Developers submit projects for review
    """
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    serializer_class = ProjectSubmitSerializer
    
    def post(self, request, id):
        """Submit project for review"""
        project = get_object_or_404(
            Project,
            id=id,
            developer=request.user,
            status=Project.Status.DRAFT
        )
        
        serializer = self.get_serializer(instance=project, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            project = submit_project_for_review(project, request.user)
            return Response({
                'success': True,
                'message': 'Project submitted for review',
                'data': ProjectDetailSerializer(project, context={'request': request}).data
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ==================== DEVELOPER VIEWS ====================

class DeveloperProjectsView(generics.ListAPIView):
    """
    List projects for authenticated developer
    
    SRS: Developer dashboard shows their projects
    """
    serializer_class = ProjectListSerializer
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return developer's projects with all statuses"""
        return Project.objects.filter(
            developer=self.request.user
        ).select_related('developer').prefetch_related('images')


class DeveloperDashboardView(APIView):
    """
    Get developer dashboard data
    
    SRS: Developer dashboard with funding progress, investor count, etc.
    """
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    
    def get(self, request):
        """Get dashboard data"""
        try:
            dashboard_data = get_developer_dashboard_data(request.user)
            return Response({
                'success': True,
                'data': dashboard_data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ADMIN VIEWS ====================

class AdminProjectReviewView(generics.GenericAPIView):
    """
    Admin review of projects
    
    SRS: Admin can approve, reject, or request changes
    """
    permission_classes = [IsAdminUser]
    serializer_class = ProjectReviewSerializer
    
    def post(self, request, id):
        """Review project"""
        project = get_object_or_404(
            Project,
            id=id,
            status=Project.Status.PENDING_REVIEW
        )
        
        serializer = self.get_serializer(instance=project, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            project = review_project(
                project=project,
                reviewer=request.user,
                action=serializer.validated_data['action'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'success': True,
                'message': f'Project {serializer.validated_data["action"]}',
                'data': ProjectDetailSerializer(project, context={'request': request}).data
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminPendingProjectsView(generics.ListAPIView):
    """
    List projects pending review (Admin only)
    
    SRS: Admin review queue
    """
    serializer_class = ProjectListSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return projects pending review"""
        return Project.objects.filter(
            status=Project.Status.PENDING_REVIEW
        ).select_related('developer').order_by('submitted_at')


class AdminProjectArchiveView(APIView):
    """
    Archive a project (Admin only)
    
    SRS: Admin can archive projects
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, id):
        """Archive project"""
        project = get_object_or_404(Project, id=id)
        
        if project.status == Project.Status.ARCHIVED:
            return Response({
                'success': False,
                'error': 'Project is already archived'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project.status = Project.Status.ARCHIVED
        project.save()
        
        # Create audit log
        from .services import create_audit_log
        create_audit_log(
            project=project,
            actor=request.user,
            action_type='ARCHIVED',
            description=f"Project '{project.title}' archived by admin",
            request=request
        )
        
        return Response({
            'success': True,
            'message': 'Project archived successfully',
            'data': ProjectDetailSerializer(project, context={'request': request}).data
        })


# ==================== FAVORITES VIEWS ====================

class FavoriteListView(generics.ListCreateAPIView):
    """
    List and create favorites
    
    SRS: Investors can favorite projects
    """
    permission_classes = [IsInvestorUser, IsVerifiedUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FavoriteCreateSerializer
        return FavoriteSerializer
    
    def get_queryset(self):
        """Return user's favorites"""
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('project', 'project__developer')
    
    def perform_create(self, serializer):
        """Add project to favorites"""
        try:
            favorite = add_to_favorites(
                user=self.request.user,
                project=serializer.validated_data['project'],
                notes=serializer.validated_data.get('notes', '')
            )
            serializer.instance = favorite
        except ValidationError as e:
            raise ValidationError({'project': str(e)})


class FavoriteDeleteView(generics.DestroyAPIView):
    """
    Remove from favorites
    """
    permission_classes = [IsInvestorUser, IsVerifiedUser]
    lookup_field = 'project_id'
    
    def get_queryset(self):
        """Return user's favorites for deletion"""
        return Favorite.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get favorite by project ID"""
        return get_object_or_404(
            Favorite,
            user=self.request.user,
            project_id=self.kwargs['project_id']
        )


# ==================== COMPARISON VIEWS ====================

class ComparisonViewSet(viewsets.ModelViewSet):
    """
    Project comparisons
    
    SRS: Compare 2-4 projects side by side
    """
    permission_classes = [IsInvestorUser, IsVerifiedUser]
    serializer_class = ProjectComparisonSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return user's comparisons"""
        return ProjectComparison.objects.filter(
            user=self.request.user
        ).prefetch_related('projects', 'projects__developer')
    
    def perform_create(self, serializer):
        """Create comparison"""
        try:
            comparison = create_project_comparison(
                user=self.request.user,
                project_ids=serializer.validated_data['project_ids'],
                name=serializer.validated_data.get('name', ''),
                notes=serializer.validated_data.get('notes', '')
            )
            serializer.instance = comparison
        except ValidationError as e:
            raise ValidationError({'project_ids': str(e)})
    
    @action(detail=True, methods=['GET'])
    def compare(self, request, pk=None):
        """Get comparison data for side-by-side view"""
        comparison = self.get_object()
        
        try:
            from .services import get_comparison_data
            comparison_data = get_comparison_data(comparison)
            return Response({
                'success': True,
                'data': comparison_data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== RESTRICTED ACCESS VIEWS ====================

class RestrictedAccessRequestView(generics.ListCreateAPIView):
    """
    Request access to restricted project data
    
    SRS: Investors request access to restricted details
    """
    permission_classes = [IsInvestorUser, IsVerifiedUser]
    serializer_class = RestrictedAccessRequestSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return user's access requests"""
        return RestrictedAccessRequest.objects.filter(
            investor=self.request.user
        ).select_related('project', 'project__developer')
    
    def perform_create(self, serializer):
        """Create access request"""
        try:
            access_request = request_restricted_access(
                investor=self.request.user,
                project=serializer.validated_data['project'],
                purpose=serializer.validated_data.get('purpose', ''),
                requested_fields=serializer.validated_data.get('requested_fields', [])
            )
            serializer.instance = access_request
        except ValidationError as e:
            raise ValidationError({'project': str(e)})


class RestrictedAccessReviewView(generics.GenericAPIView):
    """
    Review access requests (Admin only)
    
    SRS: Admin can approve, reject, or revoke access
    """
    permission_classes = [IsAdminUser]
    serializer_class = RestrictedAccessReviewSerializer
    
    def post(self, request, id):
        """Review access request"""
        access_request = get_object_or_404(RestrictedAccessRequest, id=id)
        
        serializer = self.get_serializer(instance=access_request, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            access_request = review_access_request(
                access_request=access_request,
                reviewer=request.user,
                action=serializer.validated_data['action'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'success': True,
                'message': f'Access request {serializer.validated_data["action"]}',
                'data': RestrictedAccessRequestSerializer(access_request).data
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminAccessRequestsView(generics.ListAPIView):
    """
    List access requests for admin review
    """
    permission_classes = [IsAdminUser]
    serializer_class = RestrictedAccessRequestSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['investor__email', 'project__title']
    
    def get_queryset(self):
        """Return all access requests"""
        return RestrictedAccessRequest.objects.filter(
            status=RestrictedAccessRequest.Status.PENDING
        ).select_related('investor', 'project', 'project__developer')


# ==================== MEDIA VIEWS ====================

class ProjectMediaUploadView(APIView):
    """
    Upload project media (images or 3D models)
    
    SRS: Upload media with size and format limits
    """
    permission_classes = [IsDeveloperUser, IsVerifiedUser]
    
    def post(self, request, id):
        """Upload media file"""
        project = get_object_or_404(
            Project,
            id=id,
            developer=request.user
        )
        
        file = request.FILES.get('file')
        media_type = request.data.get('type', 'image')
        is_restricted = request.data.get('is_restricted', 'false').lower() == 'true'
        
        if not file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate file
            validate_media_file(file, media_type)
            
            # Save media
            if media_type == '3d_model':
                project.model_3d = file
                project.model_3d_size = file.size
                project.model_3d_format = file.name.split('.')[-1].lower()
                project.save()
                
                media_url = request.build_absolute_uri(project.model_3d.url)
                media_type_display = '3D Model'
            else:
                # Create project image
                image = ProjectImage.objects.create(
                    project=project,
                    image=file,
                    uploaded_by=request.user,
                    is_restricted=is_restricted
                )
                media_url = request.build_absolute_uri(image.image.url)
                media_type_display = 'Image'
            
            return Response({
                'success': True,
                'message': f'{media_type_display} uploaded successfully',
                'data': {
                    'url': media_url,
                    'type': media_type,
                    'size': file.size,
                    'name': file.name
                }
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ==================== DASHBOARD & ANALYTICS VIEWS ====================

class InvestorDashboardView(APIView):
    """
    Get investor dashboard data
    
    SRS: Investor dashboard with portfolio summary
    """
    permission_classes = [IsInvestorUser, IsVerifiedUser]
    
    def get(self, request):
        """Get dashboard data"""
        try:
            dashboard_data = get_investor_dashboard_data(request.user)
            return Response({
                'success': True,
                'data': dashboard_data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectStatisticsView(APIView):
    """
    Get project statistics
    
    SRS: Dashboard metrics derived from transactions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get project statistics"""
        try:
            # Calculate statistics
            total_projects = Project.objects.filter(status=Project.Status.APPROVED).count()
            active_projects = Project.objects.filter(
                status=Project.Status.APPROVED,
                end_date__gte=timezone.now()
            ).count()
            
            completed_projects = Project.objects.filter(
                status=Project.Status.COMPLETED
            ).count()
            
            total_funding = Project.objects.filter(
                status=Project.Status.APPROVED
            ).aggregate(
                total=Sum('shares_sold')
            )['total'] or 0
            
            # Get recent activity
            recent_projects = Project.objects.filter(
                status=Project.Status.APPROVED
            ).order_by('-created_at')[:5]
            
            recent_serializer = ProjectListSerializer(
                recent_projects,
                many=True,
                context={'request': request}
            )
            
            stats = {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'total_funding': total_funding,
                'recent_projects': recent_serializer.data
            }
            
            return Response({
                'success': True,
                'data': stats
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 3D VIEWER VIEWS ====================

class Project3DViewerView(APIView):
    """
    Get 3D model data for viewer
    
    SRS: 3D viewer with rotate, zoom, and reset controls
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, id):
        """Get 3D model data"""
        project = get_object_or_404(Project, id=id)
        
        # Check access permissions
        if not project.is_3d_public:
            from .services import check_restricted_access
            if not check_restricted_access(request.user, project):
                return Response({
                    'success': False,
                    'error': 'Access to 3D model is restricted'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if not project.model_3d:
            return Response({
                'success': False,
                'error': 'No 3D model available for this project'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare 3D viewer data
        viewer_data = {
            'model_url': request.build_absolute_uri(project.model_3d.url),
            'model_format': project.model_3d_format,
            'model_size': project.model_3d_size,
            'controls': {
                'rotate': True,
                'zoom': True,
                'pan': True,
                'reset': True,
                'auto_rotate': False
            },
            'camera': {
                'position': {'x': 5, 'y': 5, 'z': 5},
                'target': {'x': 0, 'y': 0, 'z': 0},
                'fov': 60
            },
            'lighting': {
                'ambient': 0.5,
                'directional': 0.8
            }
        }
        
        return Response({
            'success': True,
            'data': viewer_data
        })