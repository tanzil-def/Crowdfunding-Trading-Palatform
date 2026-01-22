from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample, extend_schema_view

from .models import Project, ProjectMedia
from .serializers import (
    ProjectCreateSerializer, ProjectListSerializer, ProjectUpdateSerializer,
    ProjectMediaUploadSerializer, ProjectMediaListSerializer,
    ProjectMediaRequestSerializer,
    AdminProjectListSerializer, InvestorProjectListSerializer,
    InvestorProjectDetailSerializer, ProjectActionResponseSerializer,
    ProjectRejectRequestSerializer, ProjectChangesRequestSerializer
)
from .permissions import IsDeveloper, IsProjectOwner, IsAdmin, IsInvestor
from .services import (
    validate_project_editable, submit_project_for_review,
    admin_approve_project, admin_reject_project, admin_request_changes
)
from utils.pagination import StandardResultsSetPagination
from utils.responses import success_response, error_response


@extend_schema_view(
    list=extend_schema(
        examples=[
            OpenApiExample(
                'Project List Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
                                "title": "Green Energy Park",
                                "category": "Sustainability",
                                "duration_days": 30,
                                "total_project_value": "1000000.00",
                                "total_shares": 1000,
                                "share_price": "1000.00",
                                "shares_sold": 450,
                                "remaining_shares": 550,
                                "funding_percentage": 45.0,
                                "created_at": "2026-01-20T10:00:00Z"
                            }
                        ]
                    }
                },
                response_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        examples=[
            OpenApiExample(
                'Project Detail Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
                        "title": "Green Energy Park",
                        "description": "A solar farm project focused on renewable energy.",
                        "category": "Sustainability",
                        "duration_days": 30,
                        "total_project_value": "1000000.00",
                        "total_shares": 1000,
                        "share_price": "1000.00",
                        "shares_sold": 450,
                        "remaining_shares": 550,
                        "funding_percentage": 45.0,
                        "restricted_fields": ["technical_spec", "financial_projections"],
                        "is_3d_restricted": False,
                        "has_access": True,
                        "created_at": "2026-01-20T10:00:00Z"
                    }
                },
                response_only=True,
            )
        ]
    ),
    create=extend_schema(
        examples=[
            OpenApiExample(
                'Project Creation Response Example',
                value={
                    "success": True,
                    "message": "Project created successfully",
                    "data": {
                        "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
                        "title": "New Innovation Hub",
                        "description": "Modern coworking and tech space.",
                        "category": "Technology",
                        "duration_days": 60,
                        "total_project_value": "500000.00",
                        "total_shares": 500,
                        "restricted_fields": ["revenue_model"],
                        "is_3d_restricted": True,
                        "created_at": "2026-01-20T10:00:00Z"
                    }
                },
                response_only=True,
            )
        ]
    )
)
class ProjectViewSet(viewsets.ModelViewSet):
    """
    Main ViewSet for Project operations.
    Handles Creation (Developer), Browsing (Investor), and Details.
    """
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'title', 'total_project_value', 'share_price', 'funding_percentage']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return Project.objects.none()
        
        # Action-specific querysets
        if self.action in ['list', 'compare']:
            # Browsing: Publicly approved projects
            return Project.objects.filter(status='APPROVED')
            
        if self.action == 'my_projects':
            # Developer's own projects
            return Project.objects.filter(developer=user)
            
        if self.action == 'retrieve':
            # Detail view:
            # - Developers see their own
            # - Admins see all
            # - Investors see Approved
            qs = Project.objects.all()
            if user.role == 'INVESTOR':
                return qs.filter(status='APPROVED')
            if user.role == 'DEVELOPER':
                # Developers can see their own (any status) or others (Approved)
                return qs.filter(developer=user) | qs.filter(status='APPROVED')
            return qs

        return Project.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action in ['list', 'compare']:
            return InvestorProjectListSerializer
        if self.action == 'my_projects':
            return ProjectListSerializer
        if self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        if self.action == 'retrieve':
            return InvestorProjectDetailSerializer
        if self.action == 'upload_media':
            return ProjectMediaRequestSerializer
        if self.action == 'list_media':
            return ProjectMediaListSerializer
        return ProjectListSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsDeveloper()]
        if self.action == 'my_projects':
            return [IsAuthenticated(), IsDeveloper()]
        if self.action in ['update', 'partial_update', 'submit', 'upload_media']:
            return [IsAuthenticated(), IsDeveloper(), IsProjectOwner()]
        if self.action in ['list', 'retrieve', 'compare', 'list_media']:
            return [IsAuthenticated()]  # Allow logged in users to browse
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        List projects (standardized response).
        
        For Investor and unauthenticated users: defaults to status=APPROVED only.
        Admin users can see all statuses via explicit status query param.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve project details (standardized response).
        
        If has_access is true, restricted_fields values are included in the response.
        If has_access is false, restricted_fields values are omitted or returned as null/empty to enforce access control.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new project (Developer only).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            data=serializer.data,
            message="Project created successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update an existing project (only in DRAFT or NEEDS_CHANGES status).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Validate editability using service
        validate_project_editable(instance)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            data=serializer.data,
            message="Project updated successfully"
        )

    @action(detail=False, methods=['get'], url_path='my')
    def my_projects(self, request):
        """
        List all projects created by the authenticated developer.
        """
        return self.list(request)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='project_ids',
                description='Comma-separated list of project IDs to compare (min 2, max 4)',
                required=True,
                type=OpenApiTypes.STR
            )
        ],
        examples=[
            OpenApiExample(
                'Project Comparison Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": [
                        {
                            "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
                            "title": "Green Energy Park",
                            "category": "Sustainability",
                            "total_project_value": "1000000.00",
                            "share_price": "1000.00",
                            "funding_percentage": 45.0,
                            "remaining_shares": 550
                        },
                        {
                            "id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
                            "title": "Urban Tech Hub",
                            "category": "Technology",
                            "total_project_value": "2500000.00",
                            "share_price": "2500.00",
                            "funding_percentage": 80.0,
                            "remaining_shares": 200
                        }
                    ]
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='compare')
    def compare(self, request):
        """
        Compare multiple approved projects side-by-side.
        
        For Investor and unauthenticated users: defaults to status=APPROVED only.
        Admin users can see all statuses via explicit status query param.
        """
        # Support both 'ids' and 'project_ids' for backward compatibility
        ids = request.query_params.get("project_ids") or request.query_params.get("ids", "")
        
        if not ids:
            return error_response(
                message="Please provide 'project_ids' (comma-separated 2-4 IDs)",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        if len(id_list) < 2:
             return error_response(
                message="Please provide at least 2 valid project IDs for comparison",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if len(id_list) > 4:
            id_list = id_list[:4]
            
        queryset = self.get_queryset().filter(id__in=id_list)
        serializer = self.get_serializer(queryset, many=True)
        
        return success_response(data={
            "count": queryset.count(),
            "results": serializer.data
        })

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """
        Submit a draft project for admin review.
        """
        project = self.get_object()
        try:
            submit_project_for_review(project)
            return success_response(message="Project submitted for review successfully")
        except Exception as e:
             # Map exception to response
             return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='media', parser_classes=[MultiPartParser, FormParser])
    @extend_schema(
        operation_id="upload_project_media",
        request={
            'multipart/form-data': ProjectMediaRequestSerializer,
        },
        responses={201: ProjectMediaUploadSerializer},
        description="Upload media (image, video, or 3D model) to a project. \n\n"
                    "**How to use binary upload**: \n"
                    "1. Click the 'Try it out' button. \n"
                    "2. Select the 'type' of media. \n"
                    "3. Click the 'Choose File' button for the 'file' parameter to select an asset from your computer."
    )
    def upload_media(self, request, pk=None):
        """
        Upload media (image, video, or 3D model) to a project.
        """
        project = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save using the model serializer after validation
        media = ProjectMedia.objects.create(
            project=project,
            type=serializer.validated_data['type'],
            file=serializer.validated_data['file'],
            is_restricted=serializer.validated_data['is_restricted']
        )
        
        response_serializer = ProjectMediaUploadSerializer(media)
        return success_response(
            data=response_serializer.data,
            message="Media uploaded successfully",
            status_code=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'], url_path='media/list')
    @extend_schema(
        responses=ProjectMediaListSerializer(many=True),
        examples=[
            OpenApiExample(
                'Project Media List Example',
                value={
                    "success": True,
                    "message": "Success",
                    "data": {
                        "results": [
                            {
                                "id": "a1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3",
                                "type": "IMAGE",
                                "file_url": "https://api.domain.com/media/projects/solar/cover.jpg",
                                "file_extension": "jpg",
                                "is_restricted": False,
                                "uploaded_at": "2026-01-20T10:00:00Z"
                            },
                            {
                                "id": "b2c3d4e5-f6a7-4b6c-c7d8-e9f0a1b2c3d4",
                                "type": "MODEL",
                                "file_url": "https://api.domain.com/media/projects/solar/model.glb",
                                "file_extension": "glb",
                                "is_restricted": True,
                                "uploaded_at": "2026-01-20T10:05:00Z"
                            },
                            {
                                "id": "c3d4e5f6-a7b8-4c7d-d8e9-f0a1b2c3d4e5",
                                "type": "VIDEO",
                                "file_url": "https://api.domain.com/media/projects/solar/intro.mp4",
                                "file_extension": "mp4",
                                "is_restricted": False,
                                "uploaded_at": "2026-01-20T10:10:00Z"
                            }
                        ]
                    }
                },
                response_only=True,
            )
        ],
        description="List all media for a specific project. \n\n"
                    "Note: Restricted media (e.g. 3D models, restricted videos) are only returned "
                    "if the user has been granted access via an Access Request."
    )
    def list_media(self, request, pk=None):
        """
        List all media for a specific project.
        """
        project = self.get_object()
        queryset = ProjectMedia.objects.filter(project=project)
        
        # Filter restricted if no access
        user = request.user
        has_access = False
        if user.role == 'ADMIN' or user == project.developer:
            has_access = True
        elif user.role == 'INVESTOR':
            from apps.access_requests.models import AccessRequest
            has_access = AccessRequest.objects.filter(
                investor=user, project=project, status='APPROVED'
            ).exists()
            
        if not has_access:
            queryset = queryset.filter(is_restricted=False)
            
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data={
            "count": queryset.count(),
            "results": serializer.data
        })


class AdminProjectViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Admin Project Review operations.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Project.objects.all()
    serializer_class = AdminProjectListSerializer
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], url_path='projects/pending')
    def pending_projects(self, request):
        """
        List all projects pending admin review.
        """
        queryset = Project.objects.filter(status='PENDING').order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve a pending project.
        """
        project = self.get_object()
        try:
            admin_approve_project(project, request.user)
            return success_response(message="Project approved successfully")
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject', serializer_class=ProjectRejectRequestSerializer)
    def reject(self, request, pk=None):
        """
        Reject a pending project.
        """
        project = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')
        try:
            admin_reject_project(project, request.user, reason)
            return success_response(message="Project rejected successfully")
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='request-changes', serializer_class=ProjectChangesRequestSerializer)
    def request_changes(self, request, pk=None):
        """
        Request changes on a pending project.
        """
        project = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.validated_data.get('note')
        try:
            admin_request_changes(project, request.user, note)
            return success_response(message="Changes requested successfully")
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)