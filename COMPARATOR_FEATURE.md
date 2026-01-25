# 🔀 Comparator Feature – Implementation Guide

## Overview

The **Comparator Feature** allows investors to compare 2-4 projects side-by-side, enabling faster and clearer investment decisions. The backend enforces restricted field access control, ensuring sensitive data is only displayed to authorized users.

---

## 📋 Requirements

| Requirement | Status |
|------------|--------|
| Select 2–4 projects for comparison | ✅ |
| Side-by-side comparison table | ✅ Backend |
| Restricted field access control | ✅ |
| Data consistency across UI | ✅ |
| Real-time metrics | ✅ |
| "Access Required" placeholders | ✅ Backend |

---

## 🔌 API Endpoint

### GET `/api/v1/projects/compare/`

**Purpose:** Retrieve comparison data for 2-4 projects with access control.

### Request

```bash
GET /api/v1/projects/compare/?project_ids=id1,id2,id3
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_ids` | string | ✅ Yes | Comma-separated UUIDs, 2-4 projects |

**Example:**
```
GET /api/v1/projects/compare/?project_ids=71b7d9e6-f29a-46e0-9899-f0dd317403a7,8d4594d3-7a6c-430d-bfbe-d521316deba2,a1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3
```

---

### Response (200 OK)

```json
{
  "success": true,
  "message": "Projects comparison retrieved successfully",
  "data": {
    "projects": [
      {
        "id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
        "title": "Green Energy Park",
        "description": "Large scale solar farm project",
        "category": "Sustainability",
        "duration_days": 365,
        "total_project_value": "1000000.00",
        "total_shares": 1000,
        "share_price": "1000.00",
        "shares_sold": 450,
        "remaining_shares": 550,
        "funding_percentage": 45.0,
        "developer_name": "John Developer",
        "restricted_fields": ["financial_report", "blueprints"],
        "is_3d_restricted": true,
        "has_access": false,
        "created_at": "2026-01-20T10:00:00Z"
      },
      {
        "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
        "title": "Urban Tech Hub",
        "description": "Building a modern technology center",
        "category": "Technology",
        "duration_days": 540,
        "total_project_value": "2500000.00",
        "total_shares": 2500,
        "share_price": "1000.00",
        "shares_sold": 2000,
        "remaining_shares": 500,
        "funding_percentage": 80.0,
        "developer_name": "Jane Developer",
        "restricted_fields": null,
        "is_3d_restricted": false,
        "has_access": true,
        "created_at": "2026-01-18T14:30:00Z"
      }
    ],
    "restricted_fields": ["financial_report", "blueprints"]
  }
}
```

**Response Fields:**
- `success`: boolean - Request success status
- `message`: string - Status message
- `data.projects`: array - Array of ProjectComparisonSerializer objects
- `data.restricted_fields`: array - All fields that require access approval across projects

---

### Error Responses

**400 Bad Request – Missing project_ids**
```json
{
  "success": false,
  "message": "'project_ids' parameter is required (comma-separated list of 2-4 project UUIDs)"
}
```

**400 Bad Request – Too few projects**
```json
{
  "success": false,
  "message": "Please provide at least 2 project IDs for comparison"
}
```

**400 Bad Request – Too many projects**
```json
{
  "success": false,
  "message": "Maximum 4 projects can be compared at once"
}
```

**404 Not Found – Projects not approved**
```json
{
  "success": false,
  "message": "Some projects not found or not approved. Found 2 of 3"
}
```

---

## 🔐 Access Control

### Access Rules

**Admin Users:**
- ✅ Always see all restricted fields
- ✅ `has_access` = true for all projects

**Developers (Project Owners):**
- ✅ Always see their own restricted fields
- ✅ `has_access` = true for their projects
- ❌ Cannot see other projects' restricted fields

**Investors:**
- ✅ See restricted fields **only if approved access**
- ❌ See `null` values for restricted fields if access denied
- ℹ️ `has_access` = true/false based on AccessRequest status

### Example: Restricted Field Handling

**Project A** has `restricted_fields: ["financial_report"]`

**Investor WITHOUT Access:**
```json
{
  "id": "project-a",
  "title": "Project A",
  "financial_report": null,  // ← Null instead of actual data
  "has_access": false
}
```

**Investor WITH Access:**
```json
{
  "id": "project-a",
  "title": "Project A",
  "financial_report": "Detailed financial data...",
  "has_access": true
}
```

---

## 🎨 Frontend Integration

### React Component Structure

```jsx
// 1. Select Projects
<ProjectSelector 
  onSelect={(selectedIds) => {
    if (selectedIds.length >= 2 && selectedIds.length <= 4) {
      navigate(`/compare?ids=${selectedIds.join(',')}`);
    }
  }}
/>

// 2. Fetch Comparison Data
const fetchComparison = async (projectIds) => {
  const ids = projectIds.join(',');
  const response = await api.get(`/projects/compare/?project_ids=${ids}`);
  return response.data;
};

// 3. Render Comparison Table
<ComparisonTable 
  projects={projects}
  restrictedFields={restrictedFields}
  userHasAccess={hasAccess}
/>
```

### Handling "Access Required"

```jsx
const renderField = (project, fieldName) => {
  if (restrictedFields.includes(fieldName)) {
    if (!project.has_access) {
      return (
        <div className="restricted">
          <span>🔒 Access Required</span>
          <button onClick={() => requestAccess(project.id)}>
            Request Access
          </button>
        </div>
      );
    }
  }
  return project[fieldName];
};
```

---

## 🛠️ Backend Implementation Details

### Serializers

#### `ProjectComparisonSerializer`
- Used for comparator endpoint
- Respects restricted field access control
- Includes `has_access` field for UI logic
- Sets restricted fields to `null` if no access

#### `ProjectComparatorRequestSerializer`
- Validates request payload
- Ensures 2-4 project IDs
- Checks projects exist and are approved

#### `ProjectComparatorResponseSerializer`
- Documents API response structure
- Shows restricted fields list

### View Action

```python
@action(detail=False, methods=['get'], url_path='compare')
def compare(self, request):
    """
    Compare 2-4 approved projects side-by-side.
    - Validates project count (2-4)
    - Enforces access control
    - Returns restricted field list
    """
```

### Access Control Logic

```python
def get_has_access(self, obj):
    """Check if user has approved access"""
    user = self.context['request'].user
    
    # Admins and project owners always have access
    if user.role == 'ADMIN' or user == obj.developer:
        return True
    
    # Investors need approved AccessRequest
    if user.role == 'INVESTOR':
        return AccessRequest.objects.filter(
            investor=user,
            project=obj,
            status='APPROVED'
        ).exists()
    
    return False
```

---

## 📊 Database Queries

### Query Optimization

```python
# Efficient query with select_related
queryset = Project.objects.select_related('developer').filter(
    status='APPROVED',
    id__in=project_ids
)

# Prefetch access requests for current user
from django.db.models import Prefetch
AccessRequest.objects.filter(
    investor=request.user,
    status='APPROVED'
).values_list('project_id', flat=True)
```

---

## ✅ Test Cases

### Test 1: Valid Comparison (2 Projects)
```python
GET /api/v1/projects/compare/?project_ids=id1,id2
Expected: 200 OK, both projects returned
```

### Test 2: Valid Comparison (4 Projects)
```python
GET /api/v1/projects/compare/?project_ids=id1,id2,id3,id4
Expected: 200 OK, all projects returned
```

### Test 3: Too Many Projects (5 Projects)
```python
GET /api/v1/projects/compare/?project_ids=id1,id2,id3,id4,id5
Expected: 400 Bad Request, "Maximum 4 projects..."
```

### Test 4: Restricted Field Access (No Access)
```
Investor requests project with restricted_fields
Expected: restricted field values = null, has_access = false
```

### Test 5: Restricted Field Access (With Access)
```
Investor with approved AccessRequest
Expected: restricted field values populated, has_access = true
```

### Test 6: Unapproved Project
```
GET /api/v1/projects/compare/?project_ids=draft_id,approved_id
Expected: 404 Not Found, "Some projects not found or not approved"
```

---

## 🚀 Deployment Checklist

- [ ] Serializers imported in views
- [ ] `compare` action returns proper response format
- [ ] Access control enforced via `ProjectComparisonSerializer`
- [ ] Restricted fields set to null when access denied
- [ ] Test with 2, 3, 4, and 5 projects
- [ ] Test with and without access approval
- [ ] Test with admin, developer, investor roles
- [ ] Frontend receives `restricted_fields` list
- [ ] "Request Access" button shown for restricted fields
- [ ] Comparison table renders correctly

---

## 📚 References

- **API Endpoint**: `/api/v1/projects/compare/`
- **Serializers**: `ProjectComparisonSerializer`, `ProjectComparatorResponseSerializer`
- **View Action**: `ProjectViewSet.compare()`
- **Access Model**: `AccessRequest`
- **Permission**: `IsAuthenticated`

---

## 🔗 Related Features

- **Restricted Fields**: Defined in `Project.restricted_fields` (JSONField)
- **Access Requests**: Model in `apps/access_requests/`
- **Project Detail**: Uses same access control in `InvestorProjectDetailSerializer`

