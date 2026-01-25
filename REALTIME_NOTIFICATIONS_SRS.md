# Real-Time Notifications Feature - System Requirements Specification (SRS)

**Version:** 1.0.0  
**Status:** IMPLEMENTED  
**Last Updated:** January 22, 2026

---

## 1. Executive Summary

This document specifies the Real-Time Notifications Feature for the Crowdfunding Trading Platform. The system delivers instant notifications to users when relevant events occur (project approval, payments, access requests) using WebSocket technology via Django Channels. All notifications are persisted to the database and survive page reloads, providing a seamless experience across devices.

---

## 2. Purpose & Business Value

**Problem:** Users don't receive immediate feedback when important events occur (project approval, payment success/failure, access decisions). They must manually refresh to see updates.

**Solution:** Implement WebSocket-based real-time notifications with fallback to polling via REST API.

**Benefits:**
- ✅ Instant user engagement (real-time feedback)
- ✅ Reduced support queries (clear status visibility)
- ✅ Multi-device sync (read status syncs across instances)
- ✅ Persistent history (all notifications stored in database)
- ✅ Role-specific delivery (admins get admin events, investors get investor events)

---

## 3. Key Requirements

### 3.1 Notification Types

#### For Admins:
- `PROJECT_SUBMITTED` - Developer submitted a project for review
- `ACCESS_REQUESTED` - Investor requested restricted data access

#### For Developers:
- `PROJECT_APPROVED` - Project was approved by admin
- `PROJECT_REJECTED` - Project was rejected by admin
- `PROJECT_CHANGES_REQUESTED` - Admin requested changes to project

#### For Investors:
- `PAYMENT_SUCCESS` - Payment processed successfully
- `PAYMENT_FAILED` - Payment failed
- `ACCESS_APPROVED` - Restricted data access was approved
- `ACCESS_REJECTED` - Restricted data access was denied
- `ACCESS_REVOKED` - Previously approved access was revoked

#### System:
- `SYSTEM` - General system notifications

### 3.2 Delivery Methods

**Primary: WebSocket (Django Channels)**
- Real-time delivery to connected clients
- Subscription-based (one channel per user: `user_{user_id}`)
- Automatic reconnection handling

**Fallback: REST API**
- `GET /api/v1/notifications/` - List all notifications (paginated)
- `PATCH /api/v1/notifications/{id}/read/` - Mark as read (idempotent)

### 3.3 Data Persistence

All notifications must be:
- ✅ Stored in `Notification` model (PostgreSQL)
- ✅ Indexed for fast retrieval by user and timestamp
- ✅ Paginated for efficient loading
- ✅ Tracked with `is_read` status
- ✅ Queryable by type and date range

### 3.4 User Experience

- Users see new notifications instantly in real-time
- Users can mark notifications as read (idempotent operation)
- Read status syncs across all client instances
- Notifications persist across page reloads
- Unread badge/counter shows unread count

---

## 4. Current API (Unchanged)

The existing REST endpoints remain unchanged and fully functional:

```bash
# List all user notifications (paginated, 20 per page)
GET /api/v1/notifications/
Authorization: Bearer <jwt_token>
Response: {
  "success": true,
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "uuid",
        "type": "PROJECT_APPROVED",
        "title": "Project Approved",
        "message": "Your project '...' has been approved",
        "is_read": false,
        "created_at": "2026-01-20T15:30:00Z"
      }
    ]
  }
}

# Mark notification as read (idempotent - safe to repeat)
PATCH /api/v1/notifications/{notification_id}/read/
Authorization: Bearer <jwt_token>
Response: {
  "success": true,
  "message": "Notification marked as read"
}
```

---

## 5. WebSocket Connection Flow

### 5.1 Connection Establishment

**Endpoint:** `ws://localhost:8000/ws/notifications/?token=<jwt_token>`

**Step-by-Step:**

1. Client generates JWT token via `/api/v1/auth/login/`
2. Client opens WebSocket: `new WebSocket('ws://localhost:8000/ws/notifications/?token=jwt_token')`
3. Consumer extracts and validates JWT token
4. Consumer authenticates user from token
5. Consumer joins group: `user_{user_id}`
6. Consumer sends connection confirmation:
   ```json
   {
     "type": "connection",
     "status": "connected",
     "user_id": "uuid",
     "message": "Connected to notification service"
   }
   ```
7. Client is ready to receive notifications

### 5.2 Message Types

#### Incoming Messages (Client → Server)

```json
// Mark notification as read
{
  "action": "mark_read",
  "notification_id": "uuid"
}

// Keep-alive ping (optional)
{
  "action": "ping"
}
```

#### Outgoing Messages (Server → Client)

```json
// New notification received
{
  "type": "notification",
  "id": "uuid",
  "type": "PROJECT_APPROVED",
  "title": "Project Approved",
  "message": "Your project '...' has been approved",
  "is_read": false,
  "created_at": "2026-01-20T15:30:00Z",
  "metadata": {
    "project_id": "uuid",
    "project_title": "Solar Farm",
    "approved_by": "admin@example.com"
  }
}

// Notification marked as read (sync across instances)
{
  "type": "notification_read",
  "notification_id": "uuid"
}

// Pong response to ping
{
  "type": "pong"
}

// Connection confirmation
{
  "type": "connection",
  "status": "connected",
  "user_id": "uuid",
  "message": "Connected to notification service"
}

// Error message
{
  "type": "error",
  "message": "error description"
}
```

### 5.3 Disconnection Handling

- Consumer automatically leaves `user_{user_id}` group on disconnect
- Client should attempt reconnection with exponential backoff
- Offline notifications are delivered when client reconnects and polls `GET /api/v1/notifications/`

---

## 6. Event Hook Integration

### 6.1 Project Events

**Location:** `apps/projects/services.py`

```python
# When project is submitted for review
submit_project_for_review(project)
  → notify_admins_project_submitted(project)
  → Creates PROJECT_SUBMITTED notifications for all admins
  → Broadcasts via WebSocket group "user_{admin_id}"

# When project is approved
admin_approve_project(project, admin_user)
  → notify_developer_project_approved(project, admin_user)
  → Creates PROJECT_APPROVED notification for developer
  → Broadcasts via WebSocket

# When project is rejected
admin_reject_project(project, admin_user, reason)
  → notify_developer_project_rejected(project, admin_user, reason)
  → Creates PROJECT_REJECTED notification for developer

# When changes are requested
admin_request_changes(project, admin_user, note)
  → notify_developer_project_changes_requested(project, admin_user, note)
  → Creates PROJECT_CHANGES_REQUESTED notification
```

### 6.2 Payment Events

**Location:** `apps/investments/services.py`

```python
# When payment succeeds
process_successful_payment(payment, gateway_payload, shares)
  → notify_investor_payment_success(investor, payment)
  → Creates PAYMENT_SUCCESS notification for investor
  → Broadcasts via WebSocket
  → Includes project_id, shares, amount in metadata

# When payment fails
process_failed_payment(payment, gateway_payload, reason)
  → notify_investor_payment_failed(investor, payment, reason)
  → Creates PAYMENT_FAILED notification
  → Includes failure reason in metadata
```

### 6.3 Access Request Events

**Location:** `apps/access_requests/services.py`

```python
# When investor requests access
create_access_request()
  → notify_admin_access_request_received(access_request)
  → Creates ACCESS_REQUESTED notification for all admins

# When access is approved
approve_access_request(access_request, admin)
  → notify_investor_access_approved(access_request)
  → Creates ACCESS_APPROVED notification for investor
  → Investor can now see restricted fields

# When access is rejected
reject_access_request(access_request, admin, reason)
  → notify_investor_access_rejected(access_request, reason)
  → Creates ACCESS_REJECTED notification

# When access is revoked
revoke_access_request(access_request, admin, reason)
  → notify_investor_access_revoked(access_request, admin)
  → Creates ACCESS_REVOKED notification
```

---

## 7. Architecture

### 7.1 Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│  - WebSocket client connected to ws://...               │
│  - Displays notifications in real-time                  │
│  - Fallback polling on disconnect                       │
└──────────────────────────┬────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
          WebSocket              REST API
          (Real-time)           (Polling)
                │                     │
                ▼                     ▼
┌─────────────────────────────────────────────────────┐
│      Django Channels (ASGI Application)              │
│  ┌──────────────────────────────────────────────┐   │
│  │  NotificationConsumer                        │   │
│  │  - Authenticates JWT token                   │   │
│  │  - Joins group: user_{user_id}               │   │
│  │  - Receives messages from channel layer      │   │
│  │  - Sends notifications to client             │   │
│  └──────────────────────────────────────────────┘   │
│                      ▲                               │
│         async_to_sync(group_send)                   │
│                      │                               │
└──────────────────────┼───────────────────────────────┘
                       │
                       │ (notification_data)
                       │
┌──────────────────────┼───────────────────────────────┐
│   Django REST Framework (WSGI Application)           │
│  ┌──────────────────────────────────────────────┐   │
│  │  Notification Event Hooks                    │   │
│  │  - notify_admins_project_submitted()         │   │
│  │  - notify_investor_payment_success()         │   │
│  │  - notify_investor_access_approved()         │   │
│  │  - etc. (10 event hooks total)               │   │
│  └───────────────────────┬──────────────────────┘   │
│                          │                           │
│         broadcast_notification(user_id, notif)       │
│                          │                           │
│  ┌──────────────────────────────────────────────┐   │
│  │  websocket_utils.py                          │   │
│  │  - broadcast_notification()                  │   │
│  │  - Sends to channel_layer.group_send()       │   │
│  └──────────────────────────────────────────────┘   │
│                          │                           │
└──────────────────────────┼──────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│     Channel Layer (Redis or In-Memory)               │
│  - Stores messages for consumer groups               │
│  - Broadcasts to all connected WebSocket clients     │
│  - Manages group subscriptions                       │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│            PostgreSQL Database                       │
│  ┌──────────────────────────────────────────────┐   │
│  │  Notification table (persistent store)       │   │
│  │  - id, user_id, type, message, is_read       │   │
│  │  - created_at, metadata                      │   │
│  │  - Indexed by (user_id, created_at)          │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 7.2 Data Flow - Project Approval Example

```
1. Admin clicks "Approve" on project
   ├─ Frontend: PATCH /api/v1/projects/{id}/approve/
   │
2. Backend: admin_approve_project(project, admin_user)
   ├─ Update project.status = 'APPROVED'
   ├─ Log admin action (audit trail)
   │
3. Event Hook: notify_developer_project_approved(project, admin_user)
   ├─ Create Notification instance in database
   ├─ Set type = 'PROJECT_APPROVED'
   ├─ Set message, title, metadata
   │
4. Real-Time Broadcasting: broadcast_notification(developer_id, notification)
   ├─ Get channel_layer = get_channel_layer()
   ├─ async_to_sync(group_send)(
   │    "user_{developer_id}",
   │    {
   │      "type": "notification.message",
   │      "notification": {
   │        "id": "...",
   │        "type": "PROJECT_APPROVED",
   │        "message": "Your project ... has been approved",
   │        "is_read": false,
   │        "created_at": "...",
   │        "metadata": {...}
   │      }
   │    }
   │  )
   │
5. Channel Layer Processing
   ├─ Matches "user_{developer_id}" group subscriptions
   ├─ Finds all WebSocket consumers in that group
   ├─ Routes message to all consumer instances
   │
6. Consumer: async notification_message(self, event)
   ├─ Extract notification data from event
   ├─ Serialize to JSON
   ├─ await self.send(json.dumps({...}))
   │
7. Client receives WebSocket message
   ├─ Parse JSON
   ├─ Update notifications state
   ├─ Show notification badge/toast
   │
8. User can mark as read
   ├─ Frontend: {"action": "mark_read", "notification_id": "..."}
   ├─ Consumer: mark_notification_read(notification_id)
   ├─ Database: UPDATE notification SET is_read = true
   ├─ Broadcast: {"type": "notification_read", "notification_id": "..."}
   └─ All client instances sync read status
```

---

## 8. Implementation Details

### 8.1 Files Created

| File | Purpose |
|------|---------|
| `apps/notifications/consumers.py` | WebSocket consumer with JWT auth |
| `apps/notifications/routing.py` | Channels URL routing configuration |
| `apps/notifications/websocket_utils.py` | Broadcasting helper functions |
| `config/asgi.py` | Main Channels ASGI application |

### 8.2 Files Modified

| File | Changes |
|------|---------|
| `apps/notifications/models.py` | Added 13 notification type choices |
| `apps/notifications/services.py` | Added 10 event hooks + broadcasting |
| `apps/projects/services.py` | Integrated event hooks (3 locations) |
| `apps/access_requests/services.py` | Integrated event hooks (3 locations) |
| `apps/investments/services.py` | Integrated event hooks (2 locations) |
| `config/settings/base.py` | Added Channels config, Redis settings |
| `requirements.txt` | Added channels==4.0.0, channels-redis==4.1.0, daphne==4.0.0 |

### 8.3 Database Changes

**New Notification Types** (13 total):
- `PROJECT_SUBMITTED`, `PROJECT_APPROVED`, `PROJECT_REJECTED`, `PROJECT_CHANGES_REQUESTED`
- `PAYMENT_SUCCESS`, `PAYMENT_FAILED`, `PAYMENT_PENDING`
- `ACCESS_APPROVED`, `ACCESS_REJECTED`, `ACCESS_REQUESTED`, `ACCESS_REVOKED`
- `SYSTEM`

**No new tables needed** - uses existing `Notification` model

**Migration:** Extends `type` field from `max_length=20` to `max_length=30`

---

## 9. Deployment & Configuration

### 9.1 Prerequisites

- ✅ PostgreSQL 16 (existing)
- ✅ Redis 6+ (for channel layer - optional in development)
- ✅ Python 3.12 (existing)
- ✅ Django 4.2.11 (existing)

### 9.2 Installation Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt
# This adds:
#   - channels==4.0.0
#   - channels-redis==4.1.0
#   - daphne==4.0.0

# 2. Create migration for updated Notification type field
python manage.py makemigrations notifications

# 3. Apply migrations
python manage.py migrate

# 4. Collect static files (production)
python manage.py collectstatic --noinput
```

### 9.3 Development vs Production

**Development (In-Memory Channel Layer):**
```python
# No Redis required
# settings.py automatically uses InMemoryChannelLayer when DEBUG=True
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

**Production (Redis Channel Layer):**
```python
# Redis must be running
# docker run -d -p 6379:6379 redis:latest

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

### 9.4 Running the Application

**Development with Django Channels:**
```bash
# Run with Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Or with channels in development mode
python manage.py runserver
# Note: This uses WSGI only. For WebSocket, use Daphne above.
```

**Production with Gunicorn + Daphne:**
```bash
# Terminal 1: WebSocket server
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Terminal 2: WSGI server (if needed for admin)
gunicorn config.wsgi -b 127.0.0.1:8001 -w 4
```

**Docker Compose (Recommended):**
```yaml
version: '3.9'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: crowdfunding
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
```

---

## 10. Testing

### 10.1 Unit Tests

```python
# apps/notifications/tests.py
def test_notification_creation():
    """Verify notification is created and persisted"""
    
def test_websocket_auth():
    """Verify WebSocket rejects invalid JWT"""
    
def test_mark_read_idempotency():
    """Verify marking read twice doesn't error"""
    
def test_broadcast_delivery():
    """Verify notification is broadcast to correct user"""
    
def test_group_subscription():
    """Verify consumer joins correct group"""
```

### 10.2 Integration Tests

```bash
# Test project approval notification flow
1. Create project as developer
2. Submit for review
3. Admin approves project
4. Verify PROJECT_APPROVED notification created
5. Verify notification broadcast to developer
6. Connect as developer and receive notification via WebSocket

# Test payment notification flow
1. Investor initiates payment
2. Simulate payment gateway callback
3. Verify PAYMENT_SUCCESS notification created
4. Verify broadcast to investor

# Test access request notification flow
1. Investor requests access
2. Verify ACCESS_REQUESTED notification created for admins
3. Admin approves access
4. Verify ACCESS_APPROVED notification created for investor
```

### 10.3 Manual Testing (Postman/cURL)

```bash
# 1. Connect to WebSocket (in browser console)
const ws = new WebSocket('ws://localhost:8000/ws/notifications/?token=your_jwt_token');
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

# 2. Trigger an event (in another tab)
curl -X PATCH http://localhost:8000/api/v1/projects/{id}/approve/ \
  -H "Authorization: Bearer admin_token"

# 3. See notification appear in WebSocket
# Output: {
#   "type": "notification",
#   "id": "...",
#   "type": "PROJECT_APPROVED",
#   ...
# }

# 4. Poll REST API as fallback
curl http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer developer_token"
```

---

## 11. Acceptance Criteria

- ✅ **Real-time Delivery**: Notifications appear instantly when events occur
- ✅ **Persistence**: All notifications stored in database (survive reload)
- ✅ **Read Status**: Users can mark as read, idempotent operation
- ✅ **Role-based**: Only relevant notification types sent to each role
- ✅ **Multi-device**: Read status syncs across all instances of a user
- ✅ **API Compatibility**: Existing REST endpoints unchanged
- ✅ **Graceful Degradation**: Polling API works when WebSocket unavailable
- ✅ **Metadata Tracking**: All events include relevant context (project_id, etc.)
- ✅ **Error Handling**: Invalid JWT, malformed messages handled gracefully
- ✅ **Performance**: < 100ms latency for notification delivery

---

## 12. Future Enhancements

- [ ] Email notifications (for offline users)
- [ ] SMS notifications (optional)
- [ ] Notification preferences (user can toggle notification types)
- [ ] Notification categories/filtering
- [ ] Batch notifications (digest emails)
- [ ] Notification templates for i18n
- [ ] Analytics (which notifications drive engagement)
- [ ] Push notifications (browser/mobile)

---

## 13. Support & Troubleshooting

### Common Issues

**WebSocket connection fails with 403:**
- Verify JWT token is valid
- Check token hasn't expired
- Ensure Authorization header format is correct

**Notifications not appearing:**
- Verify Redis is running (production)
- Check Daphne is running (not runserver)
- Verify consumer group subscriptions in logs

**Database queries slow:**
- Add index on (user_id, created_at)
- Consider archiving old notifications (> 6 months)
- Implement pagination limits

### Debugging

```python
# Enable Django Channels debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Test channel layer connectivity
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> async def test():
...     await channel_layer.group_send("test", {"type": "test.message"})
>>> import asyncio
>>> asyncio.run(test())
```

---

## 14. References

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket MDN Reference](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [Crowdfunding Platform SRS v1.0](../README.md)

---

**Document Owner:** Backend Team  
**Review Frequency:** Quarterly  
**Last Reviewed:** January 22, 2026
