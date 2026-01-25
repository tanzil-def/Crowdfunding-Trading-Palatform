"""
WebSocket utilities for broadcasting notifications to connected users.
"""
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_notification(user_id, notification):
    """
    Broadcast a notification to a specific user's WebSocket connection.
    
    Called from: notifications.services.create_notification()
    
    Args:
        user_id: User ID to notify
        notification: Notification model instance
    """
    channel_layer = get_channel_layer()
    
    # Construct notification data
    notification_data = {
        'id': str(notification.id),
        'type': notification.type,
        'title': notification.title,
        'message': notification.message,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
        'metadata': notification.metadata,
    }
    
    # Send to user's notification group
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notification.message",
            "notification": notification_data,
        }
    )


def broadcast_notification_read(user_id, notification_id):
    """
    Broadcast that a notification was marked as read.
    Used to sync read status across all client instances of a user.
    
    Args:
        user_id: User ID
        notification_id: Notification ID marked as read
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notification.read",
            "notification_id": str(notification_id),
        }
    )
