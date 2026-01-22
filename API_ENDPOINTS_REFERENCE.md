# API Endpoints Reference Guide

## Base URL
```
http://localhost:8000/api/v1
```

---

## 🔐 Authentication Endpoints
**Base:** `/auth/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register/` | User registration |
| POST | `/auth/login/` | User login |
| POST | `/auth/logout/` | User logout |
| POST | `/auth/refresh/` | Refresh access token |
| POST | `/auth/verify-email/` | Verify email |
| GET | `/auth/profile/` | Get user profile |

---

## 📁 Projects Endpoints
**Base:** `/projects/`

### Developer - Project Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/projects/` | Create new project |
| GET | `/projects/` | List user's projects |
| GET | `/projects/my/` | List my projects (detail) |
| GET | `/projects/{id}/` | Get project details |
| PATCH | `/projects/{id}/` | Update project |
| POST | `/projects/{id}/submit/` | Submit project for review |

### Developer - Project Media
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/projects/{id}/media/` | Upload media (image/3D model) |
| GET | `/projects/{id}/media/list/` | List project media |

### Admin - Project Review
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/projects/admin/projects/pending/` | List pending projects |
| POST | `/projects/admin/projects/{id}/approve/` | Approve project |
| POST | `/projects/admin/projects/{id}/reject/` | Reject project |
| POST | `/projects/admin/projects/{id}/request-changes/` | Request changes |

### Investor - Project Discovery
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/projects/browse/` | Browse all projects |
| POST | `/projects/compare/` | Compare projects |
| GET | `/projects/{id}/detail/` | Get project detail (investor view) |

---

## 💰 Investments Endpoints
**Base:** `/investments/`

### Investor - Investment
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/investments/initiate/` | Initiate investment |
| GET | `/investments/my/` | List my investments |
| GET | `/investments/{id}/` | Get investment detail |
| GET | `/investments/portfolio/summary/` | Get portfolio summary |

### Payment Gateway
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/investments/payments/callback/` | Payment gateway callback (webhook) |

### Admin - Payment Transactions
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/investments/admin/transactions/` | List all transactions |
| GET | `/investments/admin/transactions/{id}/` | Get transaction detail |

---

## 🔐 Access Requests Endpoints
**Base:** `/access-requests/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/access-requests/` | Create access request |
| GET | `/access-requests/my/` | List my access requests |
| POST | `/access-requests/admin/{id}/approve/` | Approve request (admin) |
| POST | `/access-requests/admin/{id}/reject/` | Reject request (admin) |
| POST | `/access-requests/admin/{id}/revoke/` | Revoke access (admin) |

---

## ⭐ Favorites Endpoints
**Base:** `/favorites/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/favorites/` | Add to favorites |
| GET | `/favorites/` | List favorites |
| DELETE | `/favorites/{id}/` | Remove from favorites |

---

## 📊 Dashboard Endpoints
**Base:** `/dashboard/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/dashboard/developer/` | Developer dashboard data |
| GET | `/dashboard/investor/` | Investor dashboard data |
| GET | `/dashboard/admin/` | Admin dashboard data |

---

## 📋 Audit Logs Endpoints
**Base:** `/audit/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/audit/admin/audit-logs/` | List audit logs (admin only) |

---

## 🔔 Notifications Endpoints
**Base:** `/notifications/`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/notifications/` | List notifications |
| PATCH | `/notifications/{id}/` | Mark as read |
| DELETE | `/notifications/{id}/` | Delete notification |

---

## ✅ Common Issues & Fixes

### Issue 1: 405 Method Not Allowed
- **Cause:** Endpoint exists but doesn't support the HTTP method
- **Solution:** Check the table above to ensure you're using the correct method (GET, POST, PATCH, etc.)

### Issue 2: 404 Not Found
- **Cause:** Endpoint path is incorrect
- **Solution:** Reference this document for exact paths

### Issue 3: 403 Forbidden
- **Cause:** Missing or invalid authentication token
- **Solution:** Ensure `Authorization: Bearer <token>` header is included in requests

### Issue 4: 400 Bad Request
- **Cause:** Missing or invalid request body parameters
- **Solution:** Check request payload matches the serializer requirements

---

## 🔑 Authentication Header
All endpoints (except `/auth/login/` and `/auth/register/`) require:

```
Authorization: Bearer <your_access_token>
```

---

## 📝 Example Requests

### Create Investment
```bash
POST /api/v1/investments/initiate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
  "shares_requested": 5,
  "idempotency_key": "inv-unique-key-001"
}
```

### Payment Callback (from Gateway)
```bash
POST /api/v1/investments/payments/callback/
Content-Type: application/json

{
  "payment_reference_id": "inv-1001",
  "success": true,
  "gateway_payload": {
    "shares_requested": 2,
    "project_id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
    "investor_id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
    "txn_id": "TXN001",
    "amount": "93.06"
  }
}
```

### Get Portfolio Summary
```bash
GET /api/v1/investments/portfolio/summary/
Authorization: Bearer <token>
```

### Get Audit Logs
```bash
GET /api/v1/audit/admin/audit-logs/
Authorization: Bearer <token>
```

---

## 🚀 Swagger/OpenAPI Documentation
Visit: `http://localhost:8000/api/swagger/` for interactive API documentation.
