from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Favorite
from .serializers import (
    FavoriteCreateSerializer,
    FavoriteListSerializer
)
from .permissions import IsInvestor


# POST /favorites/
class FavoriteCreateView(generics.CreateAPIView):
    serializer_class = FavoriteCreateSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Project added to favorites"
        }, status=status.HTTP_201_CREATED)


# GET /favorites/
class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteListSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def get_queryset(self):
        return Favorite.objects.filter(investor=self.request.user)


# DELETE /favorites/{id}/
class FavoriteDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsInvestor]
    lookup_field = 'id'

    def get_queryset(self):
        return Favorite.objects.filter(investor=self.request.user)

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Favorite removed"
        })
