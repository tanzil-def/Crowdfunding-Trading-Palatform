# Real-Time Notifications - Developer Quick Reference

**Quick Start:** 5-minute integration guide

---

## 1. Installation (2 minutes)

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Run with Daphne (supports WebSocket)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

---

## 2. Frontend Integration (3 minutes)

### JavaScript/React Example

```javascript
// 1. Connect to WebSocket after login
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

// 2. Handle incoming notifications
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connection':
      console.log('Connected to notifications:', data);
      break;
      
    case 'notification':
      console.log('New notification:', data);
      // Show toast/badge/sound
      showNotificationToast(data);
      updateUnreadCount(data);
      break;
      
    case 'notification_read':
      console.log('Notification marked as read:', data.notification_id);
      // Sync read status in UI
      break;
      
    case 'error':
      console.error('WebSocket error:', data.message);
      // Fallback to polling
      startPolling();
      break;
  }
};

// 3. Send mark-as-read command
function markAsRead(notificationId) {
  ws.send(JSON.stringify({
    action: 'mark_read',
    notification_id: notificationId
  }));
}

// 4. Keep-alive ping (every 30 seconds)
setInterval(() => {
  ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);

// 5. Fallback to polling when WebSocket unavailable
function startPolling() {
  setInterval(async () => {
    const response = await fetch('/api/v1/notifications/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    // Update UI with notifications
  }, 5000); // Poll every 5 seconds
}
```

### React Hook Example

```javascript
import { useEffect, useState, useRef } from 'react';

export function useNotifications(token) {
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    ws.current = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

    ws.current.onopen = () => {
      console.log('✓ Connected to notifications');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'notification') {
        // Add new notification
        setNotifications(prev => [data, ...prev]);
      } else if (data.type === 'notification_read') {
        // Mark notification as read
        setNotifications(prev =>
          prev.map(notif =>
            notif.id === data.notification_id
              ? { ...notif, is_read: true }
              : notif
          )
        );
      }
    };

    ws.current.onerror = () => {
      setIsConnected(false);
      // Fallback to REST API polling
    };

    return () => ws.current?.close();
  }, [token]);

  const markAsRead = (notificationId) => {
    ws.current?.send(JSON.stringify({
      action: 'mark_read',
      notification_id: notificationId
    }));
  };

  return { notifications, isConnected, markAsRead };
}

// Usage in component
function NotificationCenter() {
  const { notifications, isConnected, markAsRead } = useNotifications(token);
  
  return (
    <div>
      <h2>Notifications {!isConnected && '(Offline)'}</h2>
      {notifications.map(notif => (
        <NotificationItem
          key={notif.id}
          notification={notif}
          onRead={() => markAsRead(notif.id)}
        />
      ))}
    </div>
  );
}
```

---

## 3. Notification Types at a Glance

| Type | Who Gets It | When | Action |
|------|------------|------|--------|
| `PROJECT_SUBMITTED` | Admins | Developer submits project | Review in dashboard |
| `PROJECT_APPROVED` | Developer | Admin approves project | Project is now live ✓ |
| `PROJECT_REJECTED` | Developer | Admin rejects project | See reason & resubmit |
| `PROJECT_CHANGES_REQUESTED` | Developer | Admin requests changes | Update project |
| `PAYMENT_SUCCESS` | Investor | Payment processed | Shares allocated ✓ |
| `PAYMENT_FAILED` | Investor | Payment declined | Retry payment |
| `ACCESS_APPROVED` | Investor | Admin approves access | View restricted data ✓ |
| `ACCESS_REJECTED` | Investor | Admin denies access | See reason |
| `ACCESS_REQUESTED` | Admins | Investor requests access | Make decision |
| `ACCESS_REVOKED` | Investor | Admin revokes access | Access removed |
| `SYSTEM` | All | General announcements | Platform updates |

---

## 4. REST API Fallback

When WebSocket is unavailable, use REST API:

```bash
# List all notifications (paginated)
curl http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer $TOKEN"

# Mark as read
curl -X PATCH http://localhost:8000/api/v1/notifications/{id}/read/ \
  -H "Authorization: Bearer $TOKEN"
```

Response format:
```json
{
  "success": true,
  "data": {
    "count": 5,
    "next": null,
    "results": [
      {
        "id": "uuid",
        "type": "PROJECT_APPROVED",
        "title": "Project Approved",
        "message": "Your project has been approved!",
        "is_read": false,
        "created_at": "2026-01-20T15:30:00Z",
        "metadata": {
          "project_id": "uuid",
          "approved_by": "admin@example.com"
        }
      }
    ]
  }
}
```

---

## 5. Backend Integration (for Django developers)

### Creating Notifications

```python
from apps.notifications.services import notify_investor_payment_success

# Automatically creates notification + broadcasts via WebSocket
notify_investor_payment_success(investor, payment_transaction)
```

### Available Event Hooks

```python
# Projects
notify_admins_project_submitted(project)
notify_developer_project_approved(project, admin)
notify_developer_project_rejected(project, admin, reason)
notify_developer_project_changes_requested(project, admin, changes)

# Payments
notify_investor_payment_success(investor, payment)
notify_investor_payment_failed(investor, payment, reason)

# Access Requests
notify_admin_access_request_received(access_request)
notify_investor_access_approved(access_request)
notify_investor_access_rejected(access_request, reason)
notify_investor_access_revoked(access_request, admin)
```

---

## 6. Deployment Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Set `DEBUG=False` in production
- [ ] Configure Redis connection (production only)
- [ ] Run Daphne instead of runserver
- [ ] Set `ALLOWED_HOSTS` to include WebSocket domain
- [ ] Update `CORS_ALLOWED_ORIGINS` for WebSocket
- [ ] Test WebSocket connection with browser console

---

## 7. Architecture Diagram

```
WebSocket Client        REST API Client
      │                       │
      ▼                       ▼
   ws://...          GET /api/v1/notifications/
      │                       │
      └───────────┬───────────┘
                  │
         ┌────────▼────────┐
         │  Django ASGI    │
         │  (Daphne)       │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   Channels      │
         │   Consumer      │
         └────────┬────────┘
                  │
         ┌────────▼────────────┐
         │   Channel Layer     │
         │   (Redis/Memory)    │
         └────────┬────────────┘
                  │
         ┌────────▼────────┐
         │  PostgreSQL     │
         │  Notification   │
         │  Table          │
         └─────────────────┘
```

---

## 8. Testing WebSocket (Browser Console)

```javascript
// 1. Get token from localStorage
const token = localStorage.getItem('access_token');

// 2. Open WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

// 3. Log all messages
ws.onmessage = (e) => console.log(JSON.parse(e.data));

// 4. Test mark-as-read
ws.send(JSON.stringify({
  action: 'mark_read',
  notification_id: 'your-notification-id'
}));

// 5. Test ping/pong
ws.send(JSON.stringify({ action: 'ping' }));

// 6. Close connection
ws.close();
```

---

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| WebSocket connection fails | Check JWT token, verify Daphne is running |
| Notifications not appearing | Ensure Redis running (production), check consumer logs |
| Read status not syncing | Verify `mark_read` command sent correctly |
| High latency | Check Redis connection, consider connection pooling |
| Database migrations fail | Run `python manage.py migrate --fake notifications 0001` |

---

## 10. Performance Tips

✅ **Do:**
- Use connection pooling for Redis
- Index notifications by (user_id, created_at)
- Paginate notification lists (20 per page default)
- Archive notifications older than 6 months
- Use keep-alive pings to detect stale connections

❌ **Don't:**
- Subscribe to notifications you don't need
- Query all notifications at once (always paginate)
- Keep WebSocket open for inactive users
- Store sensitive data in metadata

---

## 11. Files Reference

| File | Purpose |
|------|---------|
| `apps/notifications/consumers.py` | WebSocket consumer |
| `apps/notifications/routing.py` | URL routing |
| `apps/notifications/websocket_utils.py` | Broadcasting helpers |
| `apps/notifications/services.py` | Event hooks |
| `config/asgi.py` | ASGI application |
| `config/settings/base.py` | Channels config |

---

**Last Updated:** January 22, 2026  
**Questions?** See REALTIME_NOTIFICATIONS_SRS.md for detailed documentation
