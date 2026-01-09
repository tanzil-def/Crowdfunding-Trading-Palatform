from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Project, ProjectMedia
from .serializers import (
    ProjectCreateSerializer, ProjectListSerializer, ProjectUpdateSerializer,
    ProjectMediaUploadSerializer, ProjectMediaListSerializer,
    AdminProjectListSerializer, InvestorProjectListSerializer, InvestorProjectDetailSerializer
)
from .permissions import IsDeveloper, IsProjectOwner, IsAdmin
from .services import (
    validate_project_editable, submit_project_for_review,
    admin_approve_project, admin_reject_project, admin_request_changes
)
from apps.favorites.permissions import IsInvestor


# ------------------ Developer Project ------------------
class ProjectCreateView(generics.CreateAPIView):
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Project created",
            "data": res.data
        }, status=status.HTTP_201_CREATED)


class MyProjectListView(generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user).order_by("-created_at")


class ProjectUpdateView(generics.UpdateAPIView):
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]
    lookup_field = "id"

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user)

    def perform_update(self, serializer):
        validate_project_editable(self.get_object())
        serializer.save()


class ProjectSubmitView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsDeveloper, IsProjectOwner]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id, developer=request.user)
        submit_project_for_review(project)
        return Response({"success": True, "message": "Submitted for review"})


# ------------------ Project Media ------------------
class ProjectMediaUploadView(generics.CreateAPIView):
    serializer_class = ProjectMediaUploadSerializer
    permission_classes = [IsAuthenticated, IsDeveloper]
    parser_classes = [MultiPartParser, FormParser]  # <-- for file upload

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs["id"], developer=self.request.user)
        serializer.save(project=project)


class ProjectMediaListView(generics.ListAPIView):
    serializer_class = ProjectMediaListSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, id=self.kwargs["id"])
        qs = ProjectMedia.objects.filter(project=project)
        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(is_restricted=False)
        if user.role == "ADMIN" or user == project.developer:
            return qs
        return qs.filter(is_restricted=False)


# ------------------ Admin ------------------
class AdminPendingProjectListView(generics.ListAPIView):
    serializer_class = AdminProjectListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Project.objects.filter(status="PENDING").order_by("-created_at")


class AdminProjectApproveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_approve_project(project)
        return Response({"success": True, "message": "Project approved"})


class AdminProjectRejectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_reject_project(project)
        return Response({"success": True, "message": "Project rejected"})


class AdminProjectRequestChangesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        admin_request_changes(project)
        return Response({"success": True, "message": "Needs changes"})


# ------------------ Investor ------------------
class InvestorProjectBrowseView(generics.ListAPIView):
    serializer_class = InvestorProjectListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        return Project.objects.filter(status="APPROVED").order_by("-created_at")


class InvestorProjectDetailView(generics.RetrieveAPIView):
    serializer_class = InvestorProjectDetailSerializer
    permission_classes = [IsAuthenticated, IsInvestor]
    lookup_field = "id"

    def get_queryset(self):
        return Project.objects.filter(status="APPROVED")


class InvestorProjectCompareView(generics.ListAPIView):
    serializer_class = InvestorProjectListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        ids = self.request.query_params.get("ids")
        if not ids:
            return Project.objects.none()
        id_list = [i.strip() for i in ids.split(",")]
        return Project.objects.filter(id__in=id_list, status="APPROVED")
