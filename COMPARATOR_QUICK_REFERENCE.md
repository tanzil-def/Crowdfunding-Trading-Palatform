# 🔀 Comparator Feature – Quick Reference

## Endpoint

```
GET /api/v1/projects/compare/?project_ids=id1,id2,id3
```

## Requirements

| Requirement | Rule |
|------------|------|
| **Project Count** | 2-4 projects minimum |
| **Project Status** | Must be APPROVED |
| **Authentication** | JWT Token required |
| **User Role** | Any (access control applied) |

---

## Request Example

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=71b7d9e6-f29a-46e0-9899-f0dd317403a7,8d4594d3-7a6c-430d-bfbe-d521316deba2' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

---

## Response Structure

```json
{
  "success": true,
  "message": "Projects comparison retrieved successfully",
  "data": {
    "projects": [
      {
        "id": "uuid",
        "title": "Project Name",
        "category": "Category",
        "duration_days": 365,
        "total_project_value": "1000000.00",
        "total_shares": 1000,
        "share_price": "1000.00",
        "shares_sold": 450,
        "remaining_shares": 550,
        "funding_percentage": 45.0,
        "developer_name": "Developer Name",
        "restricted_fields": ["field1", "field2"],
        "is_3d_restricted": true,
        "has_access": false,
        "created_at": "2026-01-20T10:00:00Z"
      }
    ],
    "restricted_fields": ["field1", "field2"]
  }
}
```

---

## Access Control Logic

### has_access Field

- **true**: User can see restricted fields
- **false**: Restricted fields are hidden (null)

### Rules by User Role

```
┌─────────┬──────────────────────┐
│  Role   │  Restricted Fields   │
├─────────┼──────────────────────┤
│ Admin   │ Always visible       │
│ Owner   │ Always visible       │
│ Investor│ Only if approved     │
└─────────┴──────────────────────┘
```

---

## Frontend Implementation

### 1. Fetch Data

```javascript
const fetchComparison = async (projectIds) => {
  const query = projectIds.join(',');
  const response = await fetch(
    `/api/v1/projects/compare/?project_ids=${query}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  return response.json();
};
```

### 2. Check Access

```javascript
const canViewField = (project, fieldName) => {
  return project.has_access || 
         !project.restricted_fields?.includes(fieldName);
};
```

### 3. Render "Access Required"

```jsx
{restrictedFields.includes(fieldName) && !project.has_access ? (
  <div className="access-required">
    <span>🔒 Access Required</span>
    <button onClick={() => requestAccess(project.id)}>
      Request Access
    </button>
  </div>
) : (
  project[fieldName]
)}
```

---

## Error Handling

| Error | Status | Message |
|-------|--------|---------|
| Missing project_ids | 400 | `'project_ids' parameter is required` |
| Too few projects | 400 | `Please provide at least 2 project IDs` |
| Too many projects | 400 | `Maximum 4 projects can be compared` |
| Unapproved projects | 404 | `Some projects not found or not approved` |
| Unauthorized | 401 | `Authentication credentials not provided` |

---

## Examples

### ✅ Valid Request (2 Projects)

```
GET /api/v1/projects/compare/?project_ids=id1,id2
Status: 200 OK
```

### ✅ Valid Request (4 Projects)

```
GET /api/v1/projects/compare/?project_ids=id1,id2,id3,id4
Status: 200 OK
```

### ❌ Too Few Projects

```
GET /api/v1/projects/compare/?project_ids=id1
Status: 400 Bad Request
Message: "Please provide at least 2 project IDs for comparison"
```

### ❌ Too Many Projects

```
GET /api/v1/projects/compare/?project_ids=id1,id2,id3,id4,id5
Status: 400 Bad Request
Message: "Maximum 4 projects can be compared at once"
```

### ❌ Unapproved Projects

```
GET /api/v1/projects/compare/?project_ids=draft_id,pending_id
Status: 404 Not Found
Message: "Some projects not found or not approved. Found 0 of 2"
```

---

## Testing in Swagger

1. Go to: `http://localhost:8000/api/swagger/`
2. Find endpoint: **GET /api/v1/projects/compare/**
3. Click "Try it out"
4. Enter project IDs: `id1,id2,id3`
5. Click "Execute"

---

## Field Visibility Matrix

```
Field Name          | Admin | Developer | Investor (No Access) | Investor (With Access)
────────────────────┼───────┼───────────┼──────────────────────┼──────────────────────
id, title           | ✅    | ✅        | ✅                   | ✅
category, duration  | ✅    | ✅        | ✅                   | ✅
funding_percentage  | ✅    | ✅        | ✅                   | ✅
restricted_field    | ✅    | ✅        | ❌ (null)            | ✅
blueprints          | ✅    | ✅        | ❌ (null)            | ✅
financial_report    | ✅    | ✅        | ❌ (null)            | ✅
```

---

## Troubleshooting

### Issue: Always getting 404

**Cause**: Projects are PENDING or DRAFT status  
**Fix**: Admin must approve projects first via `/admin/projects/{id}/approve/`

### Issue: Restricted fields showing null for everyone

**Cause**: Investor trying to view but doesn't have access  
**Fix**: Investor must request access via `/access-requests/` endpoint

### Issue: Too many results

**Cause**: Providing more than 4 project IDs  
**Fix**: Limit to maximum 4 projects per comparison

---

## Related Endpoints

- **Browse Projects**: `GET /api/v1/projects/`
- **Project Detail**: `GET /api/v1/projects/{id}/detail/`
- **Request Access**: `POST /api/v1/access-requests/`
- **Check Access**: `GET /api/v1/access-requests/`

---

## Performance Tips

✅ Use 2-3 projects for best UI performance  
✅ Cache results for 5 minutes if comparison doesn't change  
✅ Load restricted field data separately if needed  
✅ Use `select_related('developer')` in backend (already done)

