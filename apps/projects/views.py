from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from rest_framework import serializers as drf_serializers

from .models import Project, ProjectMedia
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectMediaSerializer,
    ProjectMediaCreateSerializer
)
from .permissions import (
    IsDeveloperOwner,
    CanSubmitProject,
    CanArchiveProject,
    CanManageProjectMedia
)

# =============================== Developer Projects ===============================
@extend_schema(tags=["Developer"])
class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,  # PATCH only
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Developer Project Management:
    - Create, List, Retrieve, Partial Update (PATCH)
    - Submit for Review, Archive
    """
    permission_classes = [IsAuthenticated, IsDeveloperOwner]
    serializer_class = ProjectDetailSerializer
    pagination_class = PageNumberPagination
    lookup_field = 'pk'

    def get_queryset(self):
        return Project.objects.filter(developer=self.request.user, is_archived=False).select_related('developer')

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        serializer.save(developer=self.request.user, status='DRAFT')

    @extend_schema(summary="Create New Project", request=ProjectDetailSerializer, responses={201: ProjectDetailSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="List My Projects")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Project Detail")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update Project (PATCH Only)", request=ProjectDetailSerializer(partial=True))
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status not in ['DRAFT', 'NEEDS_CHANGES']:
            return Response({"detail": "Editing not allowed in current project status."}, status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        return Response({"detail": "PUT method not allowed. Use PATCH."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(
        summary="Submit Project for Review",
        request=None,
        responses={200: inline_serializer("SubmitResponse", fields={"detail": drf_serializers.CharField(), "status": drf_serializers.CharField()})}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDeveloperOwner, CanSubmitProject])
    def submit(self, request, pk=None):
        project = self.get_object()
        project.status = 'PENDING_REVIEW'
        project.save()
        return Response({"detail": "Project submitted for review successfully.", "status": "PENDING_REVIEW"})

    @extend_schema(
        summary="Archive Project",
        request=None,
        responses={200: inline_serializer("ArchiveResponse", fields={"detail": drf_serializers.CharField(), "status": drf_serializers.CharField()})}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDeveloperOwner, CanArchiveProject])
    def archive(self, request, pk=None):
        project = self.get_object()
        project.status = 'ARCHIVED'
        project.is_archived = True
        project.save()
        return Response({"detail": "Project archived successfully.", "status": "ARCHIVED"})


# =============================== Project Media ===============================
@extend_schema(tags=["Media"])
class ProjectMediaViewSet(viewsets.GenericViewSet):
    """
    Media Management:
    - Upload, List, Delete
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectMediaSerializer

    def get_queryset(self):
        return ProjectMedia.objects.filter(is_deleted=False)

    @extend_schema(
        summary="Upload Media",
        request=ProjectMediaCreateSerializer,
        responses={201: ProjectMediaSerializer},
        examples=[
            OpenApiExample("Upload 3D Model", value={"file": "(select .glb/.gltf)", "media_type": "MODEL_3D", "is_restricted": True}, request_only=True),
            OpenApiExample("Upload Cover Image", value={"file": "(select .jpg/.png)", "media_type": "IMAGE", "is_restricted": False}, request_only=True),
            OpenApiExample("Upload Video", value={"file": "(select .mp4)", "media_type": "VIDEO", "is_restricted": False}, request_only=True)
        ]
    )
    @action(detail=True, methods=['post'], url_path='upload', permission_classes=[IsAuthenticated, IsDeveloperOwner])
    def upload_media(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        serializer = ProjectMediaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        media = serializer.save(project=project)
        return Response(ProjectMediaSerializer(media).data, status=201)

    @extend_schema(summary="List Media", responses=ProjectMediaSerializer(many=True))
    @action(detail=True, methods=['get'], url_path='media')
    def list_media(self, request, pk=None):
        project = Project.objects.get(pk=pk)
        qs = project.media.filter(is_deleted=False)
        if project.developer != request.user:
            qs = qs.filter(is_restricted=False)
        return Response(ProjectMediaSerializer(qs, many=True).data)

    @extend_schema(summary="Delete Media", request=None, responses={200: inline_serializer("DeleteResponse", fields={"detail": drf_serializers.CharField()})})
    @action(detail=False, methods=['delete'], url_path='media/(?P<media_id>\\d+)/delete', permission_classes=[IsAuthenticated, CanManageProjectMedia])
    def delete_media(self, request, media_id=None):
        try:
            media = ProjectMedia.objects.get(id=media_id, is_deleted=False)
            self.check_object_permissions(request, media)
            media.is_deleted = True
            media.save()
            return Response({"detail": "Media deleted successfully."})
        except ProjectMedia.DoesNotExist:
            return Response({"detail": "Media not found."}, status=404)
