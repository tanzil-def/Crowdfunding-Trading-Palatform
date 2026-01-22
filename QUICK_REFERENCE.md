# Quick Reference: API Error Fixes

## 📋 Summary of Issues & Fixes

### Issue 1: 405 Method Not Allowed - `/api/v1/projects/`
| Issue | Solution |
|-------|----------|
| ❌ `GET /api/v1/projects/` | ✅ `GET /api/v1/projects/my/` |
| Endpoint doesn't exist | Use correct endpoint with `/my/` suffix |

---

### Issue 2: 404 Not Found - Audit Logs  
| Issue | Solution |
|-------|----------|
| ❌ `GET /api/v1/audit-logs/` | ✅ `GET /api/v1/audit/admin/audit-logs/` |
| Incomplete path | Add `/admin/` prefix |

---

### Issue 3: 404 Not Found - Portfolio
| Issue | Solution |
|-------|----------|
| ❌ `GET /api/v1/investments/portfolio/` | ✅ `GET /api/v1/investments/portfolio/summary/` |
| Missing suffix | Add `/summary/` to endpoint |

---

### Issue 4: 404 Not Found - Pending Projects
| Issue | Solution |
|-------|----------|
| ❌ `GET /api/v1/projects/pending/` | ✅ `GET /api/v1/projects/admin/projects/pending/` |
| Missing path prefix | Add `/admin/projects/` |

---

### Issue 5: 403 Forbidden - Missing Auth Token
| Issue | Solution |
|-------|----------|
| ❌ Missing `Authorization` header | ✅ Include `Authorization: Bearer <token>` |
| No token in request | Store token from login, add to all protected requests |

---

### Issue 6: Recharts - Width/Height -1 Warning
| Issue | Solution |
|-------|----------|
| ❌ Charts rendered without height | ✅ Wrap in `<ResponsiveContainer width="100%" height={300}>` |
| No parent container height | Charts need explicit container height |

---

## 🚀 Implementation Checklist

### Step 1: Use Correct API Endpoints
```javascript
// Import from provided API client
import { 
  PROJECTS_ENDPOINTS,
  INVESTMENTS_ENDPOINTS,
  ACCESS_REQUESTS_ENDPOINTS,
  AUDIT_ENDPOINTS,
  DASHBOARD_ENDPOINTS,
  apiRequest 
} from './api-client';

// ✅ CORRECT - Use endpoints with correct paths
const projects = await apiRequest(PROJECTS_ENDPOINTS.MY_PROJECTS, 'GET');
const portfolio = await apiRequest(INVESTMENTS_ENDPOINTS.PORTFOLIO_SUMMARY, 'GET');
const logs = await apiRequest(AUDIT_ENDPOINTS.ADMIN_LOGS, 'GET');
const pending = await apiRequest(PROJECTS_ENDPOINTS.ADMIN_PENDING, 'GET');
```

### Step 2: Include Authorization Header
```javascript
// apiRequest() automatically includes token from localStorage
// Ensure token is stored after login:
localStorage.setItem('access_token', response.data.access);

// All subsequent requests will include:
// Authorization: Bearer <token>
```

### Step 3: Fix Recharts Components
```javascript
import { ResponsiveContainer, LineChart, ... } from 'recharts';

// ✅ CORRECT - Wrap in ResponsiveContainer with height
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    {/* chart content */}
  </LineChart>
</ResponsiveContainer>

// Apply CSS for parent container
// .chart-wrapper { min-height: 400px; }
```

---

## 📄 Files Created for Reference

1. **`API_ENDPOINTS_REFERENCE.md`**
   - Complete endpoint reference
   - HTTP methods for each endpoint
   - Example payloads
   - Authentication requirements

2. **`FRONTEND_API_CLIENT.js`**
   - Reusable API client for React
   - Endpoint constants
   - Helper functions for requests
   - Example usage patterns

3. **`ERROR_RESOLUTION_GUIDE.md`**
   - Detailed explanation of each error
   - Root causes
   - Step-by-step solutions
   - Code examples
   - cURL testing commands

4. **`DASHBOARD_RECHARTS_FIX.jsx`**
   - Complete Dashboard component
   - Recharts with proper container setup
   - Chart helper functions
   - Data visualization components

5. **`DASHBOARD_STYLES.css`**
   - Responsive CSS for dashboard
   - Chart container styling
   - Responsive breakpoints
   - Print-friendly styles

6. **`QUICK_REFERENCE.md`** (this file)
   - Quick lookup for common issues
   - Solution summary table
   - Implementation checklist

---

## 🔐 Authentication Flow

```javascript
// 1. Login - Get token
POST /api/v1/auth/login/
{
  "email": "user@example.com",
  "password": "password"
}
Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

// 2. Store token
localStorage.setItem('access_token', response.access);

// 3. Use token in all requests
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

// 4. Refresh when expired
POST /api/v1/auth/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 🧪 Quick Testing

### Test with cURL
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' | jq -r '.access')

# Use token in request
curl -X GET http://localhost:8000/api/v1/investments/portfolio/summary/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test with Postman
1. Login to get token
2. Copy token to Postman → Authorization → Bearer Token
3. All subsequent requests will include token
4. Test each endpoint from `API_ENDPOINTS_REFERENCE.md`

---

## ✅ Verification Steps

1. **Check Backend URLs** ✓ Done (all endpoints verified)
2. **Create API Client** ✓ Done (`FRONTEND_API_CLIENT.js`)
3. **Update Frontend Calls** → Use provided API client
4. **Include Auth Header** → Automatically included by apiRequest()
5. **Fix Charts** ✓ Done (provided Dashboard component)
6. **Test with Swagger** → Visit `/api/swagger/`

---

## 📞 Common Debugging

| Problem | Solution |
|---------|----------|
| Still getting 404 | Check endpoint path matches exactly |
| Still getting 403 | Verify token is in localStorage and not expired |
| Charts still broken | Ensure ResponsiveContainer has height property |
| API returns 400 | Validate request body has all required fields |
| CORS error | Check Django CORS settings (should be configured) |

---

## 🎯 Next Steps

1. Copy `FRONTEND_API_CLIENT.js` to your frontend project
2. Replace all API calls with functions from the client
3. Apply fixes to Dashboard component
4. Test each endpoint with correct headers
5. Monitor Network tab in DevTools
6. Verify all 6 issues are resolved

---

## 📚 Additional Resources

- **Swagger Docs:** `http://localhost:8000/api/swagger/`
- **ReDoc:** `http://localhost:8000/api/redoc/`
- **Django Logs:** Run `python manage.py runserver` to see backend errors
- **Browser DevTools:** Network tab shows actual requests/responses

---

**Status:** All critical API errors documented and solutions provided ✅
