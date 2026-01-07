from .models import Notification

def create_notification(user, type, message):
    """
    Central function to create notifications for any user.
    """
    Notification.objects.create(
        user=user,
        type=type,
        message=message
    )

def mark_notification_as_read(notification):
    notification.is_read = True
    notification.save(update_fields=['is_read'])
