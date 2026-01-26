from django.urls import path
from .views import (
    NotificationListView, 
    NotificationMarkReadView,
    NotificationUnreadCountView,
    NotificationMarkAllReadView,
    NotificationPreferenceView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications-list'),
    path('unread-count/', NotificationUnreadCountView.as_view(), name='notifications-unread-count'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notifications-mark-all-read'),
    path('preferences/', NotificationPreferenceView.as_view(), name='notifications-preferences'),
    path('<uuid:id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
