# API Error Resolution Guide

## 🚨 Issue 1: 405 Method Not Allowed on `/api/v1/projects/`

### Problem
```
GET /api/v1/projects/
Response: 405 Method Not Allowed
```

### Root Cause
The endpoint might not support GET, or you're hitting the wrong endpoint.

### Solution
✅ **Correct endpoints:**

```javascript
// List your projects (GET)
GET /api/v1/projects/my/

// Create a new project (POST)
POST /api/v1/projects/
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "My Project",
  "description": "Project description",
  "category": "technology",
  "duration_days": 90,
  "total_project_value": "100000.00",
  "total_shares": 1000
}

// Get specific project (GET)
GET /api/v1/projects/{projectId}/

// Update project (PATCH)
PATCH /api/v1/projects/{projectId}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Title"
}
```

### Frontend Code
```javascript
import { PROJECTS_ENDPOINTS, apiRequest } from './api-client';

// ❌ WRONG
const projects = await fetch(`${API_URL}/projects/`);

// ✅ CORRECT
const projects = await apiRequest(
  PROJECTS_ENDPOINTS.MY_PROJECTS,
  'GET'
);
```

---

## 🚨 Issue 2: 404 Not Found - Audit Logs

### Problem
```
GET /api/v1/audit-logs/
Response: 404 Not Found
```

### Root Cause
The endpoint path is incomplete. It should include `/admin/` prefix.

### Solution
✅ **Correct endpoint:**

```javascript
// ❌ WRONG
GET /api/v1/audit-logs/

// ✅ CORRECT
GET /api/v1/audit/admin/audit-logs/
Authorization: Bearer <admin_token>
```

### Frontend Code
```javascript
import { AUDIT_ENDPOINTS, apiRequest } from './api-client';

// ✅ CORRECT
const auditLogs = await apiRequest(
  AUDIT_ENDPOINTS.ADMIN_LOGS,
  'GET'
);
```

---

## 🚨 Issue 3: 404 Not Found - Portfolio Endpoint

### Problem
```
GET /api/v1/investments/portfolio/
Response: 404 Not Found
```

### Root Cause
Missing `/summary/` suffix in the endpoint.

### Solution
✅ **Correct endpoint:**

```javascript
// ❌ WRONG
GET /api/v1/investments/portfolio/

// ✅ CORRECT
GET /api/v1/investments/portfolio/summary/
Authorization: Bearer <token>

Response:
{
  "total_invested": "5000.00",
  "projects_invested": 3,
  "total_shares_owned": 250,
  "investment_count": 5
}
```

### Frontend Code
```javascript
import { INVESTMENTS_ENDPOINTS, apiRequest } from './api-client';

// ✅ CORRECT
const portfolio = await apiRequest(
  INVESTMENTS_ENDPOINTS.PORTFOLIO_SUMMARY,
  'GET'
);
```

---

## 🚨 Issue 4: 404 Not Found - Pending Projects

### Problem
```
GET /api/v1/projects/pending/
Response: 404 Not Found
```

### Root Cause
Missing `/admin/projects/` in the path.

### Solution
✅ **Correct endpoint:**

```javascript
// ❌ WRONG
GET /api/v1/projects/pending/

// ✅ CORRECT
GET /api/v1/projects/admin/projects/pending/
Authorization: Bearer <admin_token>

Response:
[
  {
    "id": "uuid",
    "title": "Project Title",
    "status": "PENDING",
    "developer": {
      "id": "uuid",
      "email": "developer@example.com"
    },
    "created_at": "2026-01-19T10:00:00Z"
  }
]
```

### Frontend Code
```javascript
import { PROJECTS_ENDPOINTS, apiRequest } from './api-client';

// ✅ CORRECT
const pendingProjects = await apiRequest(
  PROJECTS_ENDPOINTS.ADMIN_PENDING,
  'GET'
);
```

---

## 🚨 Issue 5: 403 Forbidden - Missing/Invalid Authorization Token

### Problem
```
GET /api/v1/access-requests/my/
Response: 403 Forbidden
```

### Root Cause
Missing or invalid Authorization header, or expired token.

### Solution

#### ✅ Correct Implementation
```javascript
// 1. Store token after login
localStorage.setItem('access_token', response.data.access);

// 2. Include in ALL protected endpoints
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json',
};

// 3. Use wrapper function
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json',
});

const response = await fetch(
  '/api/v1/access-requests/my/',
  {
    method: 'GET',
    headers: getAuthHeaders(),
  }
);
```

#### React Hook Example
```javascript
import { useAuth } from './context/AuthContext';
import { ACCESS_REQUESTS_ENDPOINTS, apiRequest } from './api-client';

function AccessRequestsList() {
  const { token } = useAuth();
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      setError('Not authenticated. Please log in.');
      return;
    }

    const fetchRequests = async () => {
      try {
        // ✅ Token is automatically included via apiRequest()
        const data = await apiRequest(
          ACCESS_REQUESTS_ENDPOINTS.MY_REQUESTS,
          'GET'
        );
        setRequests(data);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchRequests();
  }, [token]);

  if (error) return <div className="error">{error}</div>;
  return <div>{/* render requests */}</div>;
}
```

---

## 🎨 Issue 6: Recharts - Width/Height -1 Warning

### Problem
```
Recharts warning: Please ensure that the container has a height.
LineChart width="-1" height="-1"
```

### Root Cause
Recharts needs a parent container with explicit width/height.

### Solution

#### ❌ WRONG
```jsx
function DashboardCharts() {
  return (
    <div>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
      </LineChart>
    </div>
  );
}
```

#### ✅ CORRECT
```jsx
function DashboardCharts() {
  return (
    <div className="charts-container">
      {/* Wrap in ResponsiveContainer with explicit height */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>

      {/* Bar Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#82ca9d" />
        </BarChart>
      </ResponsiveContainer>

      {/* Pie Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          />
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

#### CSS Styling
```css
.charts-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  padding: 1rem;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: white;
}
```

---

## 📋 Endpoint Summary Table

| Issue | Endpoint | Fix |
|-------|----------|-----|
| 405 GET /projects/ | `/projects/my/` | Use `/my/` suffix |
| 404 /audit-logs/ | `/audit/admin/audit-logs/` | Add `/admin/` prefix |
| 404 /portfolio/ | `/investments/portfolio/summary/` | Add `/summary/` suffix |
| 404 /projects/pending/ | `/projects/admin/projects/pending/` | Add `/admin/projects/` |
| 403 Missing token | Add Authorization header | Include `Bearer <token>` |

---

## ✅ Verification Checklist

- [ ] All endpoints use full paths from this guide
- [ ] All protected endpoints include `Authorization` header
- [ ] Token is retrieved from localStorage after login
- [ ] Charts are wrapped in `ResponsiveContainer` with height
- [ ] Using provided `apiRequest()` utility function
- [ ] Tested in Postman/Thunder Client with correct headers
- [ ] Check browser DevTools Network tab for actual requests
- [ ] Token is refreshed when expired (if applicable)

---

## 🧪 Testing with cURL

```bash
# Test audit logs
curl -X GET http://localhost:8000/api/v1/audit/admin/audit-logs/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# Test portfolio summary
curl -X GET http://localhost:8000/api/v1/investments/portfolio/summary/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Test pending projects
curl -X GET http://localhost:8000/api/v1/projects/admin/projects/pending/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# Test access requests
curl -X GET http://localhost:8000/api/v1/access-requests/my/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 🚀 Next Steps

1. Update frontend API calls using `FRONTEND_API_CLIENT.js`
2. Test each endpoint with correct headers
3. Monitor browser DevTools → Network tab
4. Check backend logs: `python manage.py runserver`
5. Visit Swagger docs: `http://localhost:8000/api/swagger/`
