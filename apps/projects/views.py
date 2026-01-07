from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Project, ProjectMedia
from .serializers import (
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectUpdateSerializer,
    ProjectMediaUploadSerializer,
    ProjectMediaListSerializer,
    AdminProjectListSerializer,
    InvestorProjectListSerializer,
    InvestorProjectDetailSerializer
)
from .permissions import IsDeveloper, IsProjectOwner, IsAdmin
from .services import (
    validate_project_editable,
    submit_project_for_review,
    admin_approve_project,
    admin_reject_project,
    admin_request_changes
)
from apps.favorites.permissions import IsInvestor


# ======================================================
# Phase 2 – Developer Project
# ======================================================

class ProjectCreateView(generics.CreateAPIView):
    """Developer: Create a new project"""
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        return Response(
            {"success": True, "message": "Project created", "data": res.data},
            status=status.HTTP_201_CREATED
        )


class MyProjectListView(generics.ListAPIView):
    """Developer: List my projects"""
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user).order_by('-created_at')


class ProjectUpdateView(generics.UpdateAPIView):
    """Developer: Update project (PUT/PATCH)"""
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]
    lookup_field = 'id'

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Handles both PUT and PATCH requests.
        PATCH requests are partial updates.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        validate_project_editable(instance)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"success": True, "message": "Project updated", "data": serializer.data},
            status=status.HTTP_200_OK
        )


class ProjectSubmitView(generics.GenericAPIView):
    """Developer: Submit project for admin review"""
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id, developer=request.user)
        submit_project_for_review(project)
        return Response(
            {"success": True, "message": "Submitted for review"},
            status=status.HTTP_200_OK
        )


# ======================================================
# Phase 3 – Project Media
# ======================================================

class ProjectMediaUploadView(generics.CreateAPIView):
    serializer_class = ProjectMediaUploadSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['id'], developer=self.request.user)
        serializer.save(project=project)


class ProjectMediaListView(generics.ListAPIView):
    serializer_class = ProjectMediaListSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, id=self.kwargs['id'])
        qs = ProjectMedia.objects.filter(project=project)

        if not self.request.user.is_authenticated:
            return qs.filter(is_restricted=False)

        if self.request.user.role == 'ADMIN' or self.request.user == project.developer:
            return qs

        return qs.filter(is_restricted=False)


# ======================================================
# Phase 4 – Admin Review
# ======================================================

class AdminPendingProjectListView(generics.ListAPIView):
    serializer_class = AdminProjectListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Project.objects.filter(status='PENDING').order_by('-created_at')


class AdminProjectApproveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_approve_project(project)
        return Response(
            {"success": True, "message": "Project approved"},
            status=status.HTTP_200_OK
        )


class AdminProjectRejectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_reject_project(project)
        return Response(
            {"success": True, "message": "Project rejected"},
            status=status.HTTP_200_OK
        )


class AdminProjectRequestChangesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_request_changes(project)
        return Response(
            {"success": True, "message": "Needs changes"},
            status=status.HTTP_200_OK
        )


# ======================================================
# Phase 5 – Investor Browse / Compare
# ======================================================

class InvestorProjectBrowseView(generics.ListAPIView):
    serializer_class = InvestorProjectListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        return Pr
