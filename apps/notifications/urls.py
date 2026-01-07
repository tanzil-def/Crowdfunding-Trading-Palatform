from django.urls import path
from .views import NotificationListView, NotificationMarkReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications-list'),
    path('<uuid:id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
