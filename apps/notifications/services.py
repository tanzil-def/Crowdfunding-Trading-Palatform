from .models import Notification

def create_notification(user, notification_type, message, title=None, metadata=None):
    """
    Central function to create notifications for any user.
    """
    from .models import Notification
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        metadata=metadata or {}
    )

def mark_notification_as_read(notification):
    notification.is_read = True
    notification.save(update_fields=['is_read'])
