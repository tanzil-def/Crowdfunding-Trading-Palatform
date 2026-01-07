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
        return Notification.objects.filter(user=self.request.user)

# POST /notifications/{id}/read/ → mark as read
class NotificationMarkReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({
            "success": True,
            "message": "Notification marked as read"
        })
