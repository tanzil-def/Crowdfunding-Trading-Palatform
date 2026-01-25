# 🧪 Comparator Feature – Testing Guide

## Test Setup

### Prerequisites
- 4+ approved projects in database
- User with INVESTOR role
- JWT access token for testing
- Postman or curl installed

### Sample Project IDs
```
Project 1: 71b7d9e6-f29a-46e0-9899-f0dd317403a7 (Approved, no restrictions)
Project 2: 8d4594d3-7a6c-430d-bfbe-d521316deba2 (Approved, with restrictions)
Project 3: a1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3 (Approved, with 3D restriction)
Project 4: b2c3d4e5-f6a7-5b6c-c7d8-e9f0a1b2c3d4 (Draft - should fail)
```

---

## Test Cases

### TC-1: Valid Comparison (2 Projects)

**Test**: Compare 2 approved projects

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=71b7d9e6-f29a-46e0-9899-f0dd317403a7,8d4594d3-7a6c-430d-bfbe-d521316deba2' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \
  -H 'Content-Type: application/json'
```

**Expected Response**: 200 OK
```json
{
  "success": true,
  "message": "Projects comparison retrieved successfully",
  "data": {
    "projects": [
      {
        "id": "71b7d9e6-f29a-46e0-9899-f0dd317403a7",
        "title": "Green Energy Park",
        "has_access": false,
        "restricted_fields": ["financial_report"]
      },
      {
        "id": "8d4594d3-7a6c-430d-bfbe-d521316deba2",
        "title": "Urban Tech Hub",
        "has_access": true,
        "restricted_fields": null
      }
    ],
    "restricted_fields": ["financial_report"]
  }
}
```

**Assertions**:
- ✅ Status code is 200
- ✅ `success` is true
- ✅ 2 projects returned
- ✅ `restricted_fields` array populated
- ✅ `has_access` varies by project

---

### TC-2: Valid Comparison (4 Projects – Max Limit)

**Test**: Compare exactly 4 projects

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=id1,id2,id3,id4' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 200 OK with 4 projects

**Assertions**:
- ✅ Status code is 200
- ✅ 4 projects returned
- ✅ All projects in same response

---

### TC-3: Invalid – Too Many Projects (5 Projects)

**Test**: Attempt to compare 5 projects

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=id1,id2,id3,id4,id5' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 400 Bad Request
```json
{
  "success": false,
  "message": "Maximum 4 projects can be compared at once"
}
```

**Assertions**:
- ✅ Status code is 400
- ✅ `success` is false
- ✅ Error message is clear

---

### TC-4: Invalid – Too Few Projects (1 Project)

**Test**: Attempt to compare only 1 project

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=id1' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 400 Bad Request
```json
{
  "success": false,
  "message": "Please provide at least 2 project IDs for comparison"
}
```

**Assertions**:
- ✅ Status code is 400
- ✅ Error message instructs minimum 2 projects

---

### TC-5: Invalid – Missing project_ids Parameter

**Test**: Call endpoint without project_ids

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 400 Bad Request
```json
{
  "success": false,
  "message": "'project_ids' parameter is required (comma-separated list of 2-4 project UUIDs)"
}
```

**Assertions**:
- ✅ Status code is 400
- ✅ Parameter requirement is clear

---

### TC-6: Invalid – Non-Approved Projects

**Test**: Include draft/pending project in comparison

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=approved_id,draft_id' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 404 Not Found
```json
{
  "success": false,
  "message": "Some projects not found or not approved. Found 1 of 2"
}
```

**Assertions**:
- ✅ Status code is 404
- ✅ Message shows count mismatch

---

### TC-7: Restricted Field Access – No Approval

**Test**: Investor without access views restricted fields

```bash
# As Investor without AccessRequest approval
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=restricted_project_id,normal_project_id' \
  -H 'Authorization: Bearer {INVESTOR_TOKEN}'
```

**Expected Response**: 200 OK
```json
{
  "data": {
    "projects": [
      {
        "id": "restricted_project_id",
        "title": "Project with Restrictions",
        "has_access": false,
        "financial_report": null,    // ← Restricted field is null
        "blueprints": null,          // ← Restricted field is null
        "restricted_fields": ["financial_report", "blueprints"]
      }
    ]
  }
}
```

**Assertions**:
- ✅ Status code is 200
- ✅ `has_access` is false
- ✅ Restricted fields are null
- ✅ `restricted_fields` list shows which fields are restricted

---

### TC-8: Restricted Field Access – With Approval

**Test**: Investor with approved access views restricted fields

```bash
# As Investor WITH AccessRequest approval
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=restricted_project_id' \
  -H 'Authorization: Bearer {INVESTOR_TOKEN}'
```

**Expected Response**: 200 OK
```json
{
  "data": {
    "projects": [
      {
        "id": "restricted_project_id",
        "title": "Project with Restrictions",
        "has_access": true,
        "financial_report": "Detailed financial data...",  // ← Visible
        "blueprints": "Architectural plans...",            // ← Visible
        "restricted_fields": ["financial_report", "blueprints"]
      }
    ]
  }
}
```

**Assertions**:
- ✅ Status code is 200
- ✅ `has_access` is true
- ✅ Restricted fields contain actual data
- ✅ Data matches what's in project detail

---

### TC-9: Admin Access – Always Granted

**Test**: Admin user sees all restricted fields

```bash
# As Admin user
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=restricted_project_id' \
  -H 'Authorization: Bearer {ADMIN_TOKEN}'
```

**Expected Response**: 200 OK
```json
{
  "data": {
    "projects": [
      {
        "id": "restricted_project_id",
        "has_access": true,
        "financial_report": "...",  // ← Always visible
        "blueprints": "..."         // ← Always visible
      }
    ]
  }
}
```

**Assertions**:
- ✅ `has_access` is true regardless of AccessRequest
- ✅ All restricted fields visible
- ✅ No "Access Required" message needed

---

### TC-10: Developer (Project Owner) Access

**Test**: Project developer sees own restricted fields

```bash
# As Developer who owns restricted_project_id
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=restricted_project_id' \
  -H 'Authorization: Bearer {DEVELOPER_TOKEN}'
```

**Expected Response**: 200 OK
```json
{
  "data": {
    "projects": [
      {
        "id": "restricted_project_id",
        "has_access": true,
        "financial_report": "...",  // ← Visible (owns project)
        "blueprints": "..."
      }
    ]
  }
}
```

**Assertions**:
- ✅ `has_access` is true for own project
- ✅ All restricted fields visible
- ✅ Developer can see other's approved projects

---

### TC-11: Authentication Missing

**Test**: Call without JWT token

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=id1,id2'
```

**Expected Response**: 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Assertions**:
- ✅ Status code is 401
- ✅ Auth error message

---

### TC-12: Invalid Project UUID Format

**Test**: Use malformed UUID

```bash
curl -X GET \
  'http://localhost:8000/api/v1/projects/compare/?project_ids=not-a-uuid,also-not-uuid' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}'
```

**Expected Response**: 400 Bad Request or 404 Not Found

**Assertions**:
- ✅ Graceful error handling
- ✅ No 500 Internal Server Error

---

## Postman Collection

### Setup

1. Create Postman Environment Variables:
```
{{BASE_URL}} = http://localhost:8000
{{ACCESS_TOKEN}} = your-jwt-token
{{PROJECT_ID_1}} = 71b7d9e6-f29a-46e0-9899-f0dd317403a7
{{PROJECT_ID_2}} = 8d4594d3-7a6c-430d-bfbe-d521316deba2
```

### Request Template

```
GET {{BASE_URL}}/api/v1/projects/compare/?project_ids={{PROJECT_ID_1}},{{PROJECT_ID_2}}

Header:
Authorization: Bearer {{ACCESS_TOKEN}}
```

---

## Testing Checklist

### Basic Functionality
- [ ] 2-project comparison works
- [ ] 3-project comparison works
- [ ] 4-project comparison works
- [ ] 5+ projects rejected
- [ ] 0-1 projects rejected

### Error Handling
- [ ] Missing project_ids returns 400
- [ ] Unapproved projects return 404
- [ ] Malformed UUIDs handled gracefully
- [ ] Missing auth returns 401

### Access Control
- [ ] Investor without access sees null restricted fields
- [ ] Investor with access sees restricted fields
- [ ] Admin sees all fields
- [ ] Developer sees own restricted fields

### Data Consistency
- [ ] Metrics match project detail view
- [ ] Funding percentage calculated correctly
- [ ] Share prices consistent
- [ ] Developer names populated

### Response Format
- [ ] `success` field present and correct
- [ ] `message` field present and meaningful
- [ ] `data.projects` array returned
- [ ] `data.restricted_fields` array returned

---

## Performance Testing

### Load Test (100 comparisons)

```bash
for i in {1..100}; do
  curl -X GET \
    'http://localhost:8000/api/v1/projects/compare/?project_ids=id1,id2' \
    -H 'Authorization: Bearer {TOKEN}' \
    -w 'Time: %{time_total}s\n'
done
```

**Target**: Average response time < 200ms

---

## SQL Queries to Verify

```sql
-- Check if projects were fetched
SELECT id, title, status FROM projects 
WHERE status = 'APPROVED' 
LIMIT 5;

-- Check access requests
SELECT investor_id, project_id, status FROM access_requests 
WHERE status = 'APPROVED';

-- Verify restricted fields
SELECT id, title, restricted_fields FROM projects 
WHERE restricted_fields IS NOT NULL;
```

---

## Debugging Tips

### Enable Django Debug Logging

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Print Query Count

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    # Test code here
    pass
print(f"Queries: {len(ctx)}")
```

