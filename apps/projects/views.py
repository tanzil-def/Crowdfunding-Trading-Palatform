from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Project, ProjectMedia
from .serializers import (
    ProjectCreateSerializer, ProjectListSerializer, ProjectUpdateSerializer,
    ProjectMediaUploadSerializer, ProjectMediaListSerializer,
    AdminProjectListSerializer, InvestorProjectListSerializer,
    InvestorProjectDetailSerializer
)
from .permissions import IsDeveloper, IsProjectOwner, IsAdmin, IsInvestor
from .services import (
    validate_project_editable, submit_project_for_review,
    admin_approve_project, admin_reject_project, admin_request_changes
)
from utils.pagination import StandardResultsSetPagination


class ProjectCreateView(generics.CreateAPIView):
    """
    Create a new project (Developer only).
    """
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            "success": True,
            "message": "Project created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class MyProjectListView(generics.ListAPIView):
    """
    List all projects created by the authenticated developer.
    """
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'total_project_value']
    ordering = ['-created_at']

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user)


class ProjectUpdateView(generics.UpdateAPIView):
    """
    Update an existing project (only in DRAFT or NEEDS_CHANGES status).
    """
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]
    lookup_field = "id"

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user)

    def perform_update(self, serializer):
        validate_project_editable(self.get_object())
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            "success": True,
            "message": "Project updated successfully",
            "data": serializer.data
        })


class ProjectSubmitView(generics.GenericAPIView):
    """
    Submit a draft project for admin review.
    """
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id, developer=request.user)
        submit_project_for_review(project)
        
        return Response({
            "success": True,
            "message": "Project submitted for review successfully"
        })


class ProjectMediaUploadView(generics.CreateAPIView):
    """
    Upload media (image or 3D model) to a project.
    """
    serializer_class = ProjectMediaUploadSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        project = get_object_or_404(
            Project, 
            id=self.kwargs["id"], 
            developer=self.request.user
        )
        serializer.save(project=project)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            "success": True,
            "message": "Media uploaded successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectMediaListView(generics.ListAPIView):
    """
    List all media for a specific project.
    Filters out restricted media based on user permissions.
    """
    serializer_class = ProjectMediaListSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, id=self.kwargs["id"])
        queryset = ProjectMedia.objects.filter(project=project)
        user = self.request.user

        if not user.is_authenticated:
            return queryset.filter(is_restricted=False)
        
        if user.role == 'ADMIN' or user == project.developer:
            return queryset
        
        if user.role == 'INVESTOR':
            from apps.access_requests.models import AccessRequest
            has_access = AccessRequest.objects.filter(
                investor=user,
                project=project,
                status='APPROVED'
            ).exists()
            
            if has_access:
                return queryset
        
        return queryset.filter(is_restricted=False)


class AdminPendingProjectListView(generics.ListAPIView):
    """
    List all projects pending admin review.
    """
    serializer_class = AdminProjectListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'developer__email']
    ordering = ['-created_at']

    def get_queryset(self):
        return Project.objects.filter(status='PENDING')


class AdminProjectApproveView(generics.GenericAPIView):
    """
    Approve a pending project.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_approve_project(project, request.user)
        
        return Response({
            "success": True,
            "message": "Project approved successfully"
        })


class AdminProjectRejectView(generics.GenericAPIView):
    """
    Reject a pending project with optional reason.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        reason = request.data.get('reason')
        admin_reject_project(project, request.user, reason)
        
        return Response({
            "success": True,
            "message": "Project rejected successfully"
        })


class AdminProjectRequestChangesView(generics.GenericAPIView):
    """
    Request changes on a pending project with optional note.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        note = request.data.get('note')
        admin_request_changes(project, request.user, note)
        
        return Response({
            "success": True,
            "message": "Changes requested successfully"
        })


class InvestorProjectBrowseView(generics.ListAPIView):
    """
    Browse all approved projects (Investor only).
    Supports filtering, search, and ordering.
    """
    serializer_class = InvestorProjectListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'title', 'share_price', 'funding_percentage']
    ordering = ['-created_at']

    def get_queryset(self):
        return Project.objects.filter(status='APPROVED')


class InvestorProjectDetailView(generics.RetrieveAPIView):
    """
    View detailed information about an approved project.
    Restricted fields are filtered based on access permissions.
    """
    serializer_class = InvestorProjectDetailSerializer
    permission_classes = [IsAuthenticated, IsInvestor]
    lookup_field = "id"

    def get_queryset(self):
        return Project.objects.filter(status='APPROVED')


class InvestorProjectCompareView(generics.ListAPIView):
    """
    Compare multiple approved projects side-by-side.
    Accepts comma-separated project IDs via 'ids' query parameter.
    Example: /api/v1/projects/compare/?ids=uuid1,uuid2,uuid3
    """
    serializer_class = InvestorProjectListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        ids = self.request.query_params.get("ids", "")
        
        if not ids:
            return Project.objects.none()
        
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        
        if len(id_list) < 2:
            return Project.objects.none()
        
        if len(id_list) > 4:
            id_list = id_list[:4]
        
        return Project.objects.filter(id__in=id_list, status='APPROVED')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                "success": False,
                "message": "Please provide 2-4 valid project IDs for comparison"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data
        })