from rest_framework import generics, status, serializers, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import AccessRequest
from .serializers import (
    AccessRequestCreateSerializer,
    AccessRequestListSerializer,
    AdminAccessRequestActionSerializer,
    AccessRequestActionResponseSerializer,
    AdminAccessRequestListSerializer,
    DeveloperProjectAccessRequestSerializer
)
from .permissions import IsInvestor, IsAdmin, IsOwnerOrAdmin
from .services import approve_access_request, reject_access_request, revoke_access_request


# POST /access-requests/  (Investor Request)
class AccessRequestCreateView(generics.CreateAPIView):
    serializer_class = AccessRequestCreateSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Access request submitted"
        }, status=status.HTTP_201_CREATED)


# GET /access-requests/my/  (Investor)
class MyAccessRequestListView(generics.ListAPIView):
    serializer_class = AccessRequestListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return AccessRequest.objects.none()
        return AccessRequest.objects.filter(investor=self.request.user)


# POST /admin/access-requests/{id}/approve/
class AdminAccessRequestApproveView(generics.GenericAPIView):
    serializer_class = AdminAccessRequestActionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(request=None, responses={200: AccessRequestActionResponseSerializer})
    def post(self, request, id):
        access_request = get_object_or_404(AccessRequest, id=id)
        approve_access_request(access_request, request.user)
        return Response({
            "success": True,
            "message": "Access request approved"
        })


# POST /admin/access-requests/{id}/reject/
class AdminAccessRequestRejectView(generics.GenericAPIView):
    serializer_class = AdminAccessRequestActionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(request=AdminAccessRequestActionSerializer, responses={200: AccessRequestActionResponseSerializer})
    def post(self, request, id):
        access_request = get_object_or_404(AccessRequest, id=id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reject_access_request(access_request, request.user, serializer.validated_data.get('reason'))
        return Response({
            "success": True,
            "message": "Access request rejected"
        })


# POST /admin/access-requests/{id}/revoke/
class AdminAccessRequestRevokeView(generics.GenericAPIView):
    serializer_class = AdminAccessRequestActionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(request=AdminAccessRequestActionSerializer, responses={200: AccessRequestActionResponseSerializer})
    def post(self, request, id):
        access_request = get_object_or_404(AccessRequest, id=id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revoke_access_request(access_request, request.user, serializer.validated_data.get('reason'))
        return Response({
            "success": True,
            "message": "Access revoked"
        })


class AdminAccessRequestListView(generics.ListAPIView):
    serializer_class = AdminAccessRequestListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = AccessRequest.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['project__title', 'investor__email']


class DeveloperProjectAccessRequestListView(generics.ListAPIView):
    serializer_class = DeveloperProjectAccessRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AccessRequest.objects.none()
        project_id = self.kwargs.get('project_id')
        user = self.request.user
        
        # Admin can see all, Developers see their own
        if user.role == 'ADMIN':
            return AccessRequest.objects.filter(project_id=project_id)
        
        return AccessRequest.objects.filter(
            project_id=project_id,
            project__developer=user
        )
