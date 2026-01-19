from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Notification
from .serializers import NotificationSerializer

# GET /notifications/ → list user notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkReadView(generics.GenericAPIView):
    serializer_class = NotificationSerializer  # Added to satisfy Swagger
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({
            "success": True,
            "message": "Notification marked as read"
        })
