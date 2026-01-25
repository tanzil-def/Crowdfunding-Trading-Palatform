"""
Django Channels WebSocket consumer for real-time notifications.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    
    Connection Flow:
    1. Client connects with JWT token in URL: ws://localhost:8000/ws/notifications/?token=jwt_token
    2. Consumer authenticates the token
    3. Consumer joins user's notification group: group_name = "user_{user_id}"
    4. All notifications to that user are broadcast to this group
    5. Client receives real-time notifications as they're created
    
    Message Types:
    - notification.message: New notification received
    - notification.read: Notification marked as read (sync across instances)
    """

    async def connect(self):
        """
        Called when WebSocket connects.
        Authenticate user via JWT token and join notification group.
        """
        # Extract JWT token from query parameters
        token = self.scope.get('query_string', b'').decode('utf-8')
        
        # Try to authenticate the user
        self.user = await self.authenticate_user(token)
        
        if not self.user or self.user.is_anonymous:
            # Reject connection if unauthenticated
            await self.close(code=4001)  # Custom close code: Unauthorized
            return
        
        # Join user's notification group
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        # Accept the connection
        await self.accept()
        
        # Send connection confirmation
        await self.send(json.dumps({
            "type": "connection",
            "status": "connected",
            "user_id": str(self.user.id),
            "message": "Connected to notification service"
        }))

    async def disconnect(self, close_code):
        """Called when WebSocket disconnects."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Called when client sends a message.
        Supports commands like:
        - {"action": "mark_read", "notification_id": "..."}
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            
            elif action == 'ping':
                # Keep-alive ping/pong
                await self.send(json.dumps({"type": "pong"}))
            
            else:
                await self.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                }))
        
        except json.JSONDecodeError:
            await self.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    # ============================================================================
    # Broadcast message handlers (called by group_send)
    # ============================================================================

    async def notification_message(self, event):
        """
        Handler for notification.message type broadcast.
        Called when a new notification is created for this user.
        """
        notification = event['notification']
        
        await self.send(json.dumps({
            "type": "notification",
            **notification
        }))

    async def notification_read(self, event):
        """
        Handler for notification.read type broadcast.
        Syncs read status across client instances.
        """
        notification_id = event['notification_id']
        
        await self.send(json.dumps({
            "type": "notification_read",
            "notification_id": notification_id
        }))

    # ============================================================================
    # Database operations (async wrapper functions)
    # ============================================================================

    @database_sync_to_async
    def authenticate_user(self, token_string):
        """
        Authenticate user from JWT token.
        Returns: User instance or None
        """
        try:
            # Extract token from "token=xyz" format
            if '=' in token_string:
                _, token = token_string.split('=', 1)
            else:
                token = token_string
            
            # Decode and validate JWT
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Import here to avoid circular imports
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            return User.objects.get(id=user_id)
        
        except Exception:
            return None

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read in the database.
        Then broadcast the update to all user instances.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            
            # Broadcast read status update
            from .websocket_utils import broadcast_notification_read
            broadcast_notification_read(self.user.id, notification_id)
            
            return True
        except Notification.DoesNotExist:
            return False