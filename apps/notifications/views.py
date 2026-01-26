from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer

# GET /notifications/ → list user notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

from drf_spectacular.utils import extend_schema

class NotificationMarkReadView(generics.GenericAPIView):
    serializer_class = NotificationSerializer  # Added to satisfy Swagger
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Idempotent: Marks notification as read. Repeated calls are safe."
    )
    def patch(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({
            "success": True,
            "message": "Notification marked as read"
        })


class NotificationUnreadCountView(generics.GenericAPIView):
    serializer_class = serializers.Serializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({
            "success": True,
            "unread_count": count
        })


class NotificationMarkAllReadView(generics.GenericAPIView):
    serializer_class = serializers.Serializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            "success": True,
            "marked_count": updated,
            "message": f"{updated} notifications marked as read"
        })


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        pref, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return pref
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "data": serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "success": True,
            "message": "Preferences updated",
            "data": serializer.data
        })
