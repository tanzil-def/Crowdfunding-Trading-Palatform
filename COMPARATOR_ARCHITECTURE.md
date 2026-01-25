# 🔀 Comparator Feature – Architecture & Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vite)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ ProjectSelector  │→ │ ComparisonTable  │  │ AccessRequest │ │
│  │  (2-4 projects)  │  │  (side-by-side)  │  │ (if needed)   │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└──────────────┬──────────────────────────────────────────────────┘
               │ GET /api/v1/projects/compare/?project_ids=id1,id2,id3
               ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Backend (Django REST Framework)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           ProjectViewSet.compare() Action               │  │
│  │  1. Parse project_ids from query params                 │  │
│  │  2. Validate 2-4 projects                              │  │
│  │  3. Check all projects APPROVED                        │  │
│  │  4. Serialize with ProjectComparisonSerializer         │  │
│  └──────────┬───────────────────────────────────────────────┘  │
│             │                                                    │
│  ┌──────────▼───────────────────────────────────────────────┐  │
│  │      ProjectComparisonSerializer                        │  │
│  │  1. Check user.role (ADMIN/DEVELOPER/INVESTOR)         │  │
│  │  2. Check AccessRequest.status for INVESTOR            │  │
│  │  3. Set has_access = true/false                        │  │
│  │  4. Filter restricted_fields based on has_access      │  │
│  │  5. Return null for restricted fields if no access    │  │
│  └──────────┬───────────────────────────────────────────────┘  │
│             │                                                    │
│  ┌──────────▼───────────────────────────────────────────────┐  │
│  │         Database Queries (Optimized)                   │  │
│  │  • Project.objects.select_related('developer')         │  │
│  │    .filter(status='APPROVED', id__in=[...])           │  │
│  │  • AccessRequest.objects.filter(                      │  │
│  │    investor=user, project=project, status='APPROVED') │  │
│  └──────────┬───────────────────────────────────────────────┘  │
│             │                                                    │
│  ┌──────────▼───────────────────────────────────────────────┐  │
│  │           Database (PostgreSQL)                        │  │
│  │  • projects table (APPROVED projects only)            │  │
│  │  • access_requests table (approval status)            │  │
│  │  • users table (role lookup)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
               │ Return JSON response
               ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Response (200 OK)                           │
│  {                                                              │
│    "success": true,                                            │
│    "data": {                                                   │
│      "projects": [...],    ← Filtered by access control      │
│      "restricted_fields": [...]  ← Fields needing access     │
│    }                                                           │
│  }                                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Request/Response Flow

```
User Action              API Request              Backend Processing
───────────────────────────────────────────────────────────────────

1. Select Projects  →   GET /compare/?          Validate project_ids
   (2-4 items)          project_ids=...         (2-4 count)
                                                ↓
2. Click Compare    →                           Check status
   Button                                       (APPROVED only)
                                                ↓
3. Loading State    →                           Query database
                                                (select_related)
                                                ↓
4. Display Table    ←   200 OK Response    ←   Apply access control
                        {                      (restricted fields)
                          projects: [...]      ↓
                          restricted: [...]    Return JSON
                        }
```

---

## Access Control Decision Tree

```
                    Is user authenticated?
                           │
                    ┌──────┴──────┐
                    │             │
                   NO            YES
                    │             │
                    ↓             ↓
              Return 401    Check user.role
              Unauthorized       │
                          ┌──────┼──────┐
                          │      │      │
                        ADMIN  DEV   INVESTOR
                          │      │      │
                          ↓      ↓      ↓
                     Visible  Own    Check
                     all      only   AccessRequest
                      │        │          │
                      │        │    ┌─────┴─────┐
                      │        │    │           │
                      │        │  APPROVED    DENIED
                      │        │    │           │
                      ↓        ↓    ↓           ↓
                    ┌─────────────────────────────┐
                    │   Restricted Fields Set    │
                    │   has_access = true        │
                    │   (all fields visible)     │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                  Visible             Null (Hidden)
                (actual data)      (access required)
                                    │
                              Show "🔒 Access
                              Required" message
```

---

## Data Flow Diagram

```
INPUT VALIDATION
┌────────────────────────────────┐
│ Query Params: project_ids      │
│ Format: "id1,id2,id3"         │
└────────────┬───────────────────┘
             │
             ↓
PARSING & VALIDATION
┌────────────────────────────────┐
│ 1. Split by comma              │
│ 2. Count: 2 ≤ count ≤ 4       │
│ 3. Validate UUID format        │
└────────────┬───────────────────┘
             │
             ↓
DATABASE QUERY
┌────────────────────────────────┐
│ SELECT FROM projects           │
│ WHERE status = 'APPROVED'      │
│   AND id IN (id1, id2, id3)   │
│ SELECT_RELATED('developer')    │
└────────────┬───────────────────┘
             │
             ↓
ACCESS CONTROL CHECK
┌────────────────────────────────┐
│ FOR EACH project:              │
│  1. Get user.role              │
│  2. If INVESTOR:               │
│     Check AccessRequest        │
│  3. Set has_access             │
│  4. Filter restricted_fields   │
└────────────┬───────────────────┘
             │
             ↓
SERIALIZATION
┌────────────────────────────────┐
│ ProjectComparisonSerializer    │
│  to_representation():          │
│  - Hide restricted fields      │
│  - Set to null if no access    │
│  - Include has_access flag     │
└────────────┬───────────────────┘
             │
             ↓
RESPONSE FORMATTING
┌────────────────────────────────┐
│ {                              │
│   "success": true,             │
│   "message": "...",            │
│   "data": {                    │
│     "projects": [...],         │
│     "restricted_fields": [...]  │
│   }                            │
│ }                              │
└────────────────────────────────┘
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend                                 │
│                                                             │
│  ProjectSelector Component                                 │
│  ├─ Checkbox for each project                             │
│  ├─ Max 4 selections enforced                             │
│  ├─ "Compare" button (disabled if < 2)                    │
│  └─ onClick → navigate to /compare?ids=...               │
│                         │                                  │
│                         ↓                                  │
│  ComparisonPage Component                                  │
│  ├─ Parse URL params                                      │
│  ├─ Fetch: GET /api/v1/projects/compare/?project_ids=... │
│  ├─ Loading state                                         │
│  └─ Error handling (400/404)                             │
│                         │                                  │
│                         ↓                                  │
│  ComparisonTable Component                                 │
│  ├─ Render table                                          │
│  ├─ Projects as columns                                   │
│  ├─ Attributes as rows                                    │
│  │  ├─ title, category, duration                         │
│  │  ├─ funding_percentage, share_price                   │
│  │  └─ restricted fields (if accessible)                 │
│  │                                                        │
│  ├─ For restricted fields (has_access=false):            │
│  │  ├─ Show "🔒 Access Required" label                   │
│  │  ├─ Show "Request Access" button                      │
│  │  └─ Hide actual value                                 │
│  │                                                        │
│  └─ For restricted fields (has_access=true):             │
│     ├─ Show actual value                                 │
│     └─ Styled as accessible data                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ API Call
         ↓
┌─────────────────────────────────────────────────────────────┐
│                     Backend                                │
│                                                             │
│  ProjectViewSet.compare()                                   │
│  ├─ Parse query params                                     │
│  ├─ Validate 2-4 projects                                 │
│  ├─ Query database                                         │
│  └─ Call ProjectComparisonSerializer                      │
│                          │                                 │
│                          ↓                                 │
│  ProjectComparisonSerializer                               │
│  ├─ get_has_access():                                      │
│  │  ├─ If ADMIN/owner → true                              │
│  │  ├─ If INVESTOR → check AccessRequest → true/false    │
│  │  └─ Return boolean                                      │
│  │                                                        │
│  └─ to_representation():                                   │
│     ├─ If has_access=false:                               │
│     │  └─ Set restricted fields to null                   │
│     └─ Return serialized data                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
Request → Validation
  │
  ├─ Missing project_ids?
  │  └─ 400 Bad Request: "parameter required"
  │
  ├─ Non-UUID format?
  │  └─ 400 Bad Request or 404
  │
  ├─ Less than 2 projects?
  │  └─ 400 Bad Request: "at least 2 required"
  │
  ├─ More than 4 projects?
  │  └─ 400 Bad Request: "maximum 4 allowed"
  │
  ├─ Project not found?
  │  └─ 404 Not Found: "Some projects not found"
  │
  ├─ Project not APPROVED?
  │  └─ 404 Not Found: "not approved"
  │
  ├─ No authentication?
  │  └─ 401 Unauthorized: "credentials not provided"
  │
  └─ Success?
     └─ 200 OK: Return comparison data
```

---

## Performance Optimization

```
Single Request Lifetime
────────────────────────────────────────────────

1. Parse & Validate (< 5ms)
   ├─ Split query string
   └─ Count validation

2. Database Query (< 20ms for 4 projects)
   ├─ SELECT projects WHERE status='APPROVED' AND id IN (...)
   ├─ SELECT_RELATED('developer') - single query
   └─ Index on (status, id) - fast lookup

3. Access Control (< 10ms)
   ├─ Check user.role - cached in JWT
   └─ Query AccessRequest if INVESTOR - indexed on (investor, project, status)

4. Serialization (< 5ms)
   ├─ Loop through projects
   ├─ Filter restricted fields
   └─ Convert to JSON

5. Response (< 10ms)
   └─ Return to client

TOTAL: < 50ms for 4-project comparison

Optimization Strategies:
✅ select_related('developer') - prevents N+1 queries
✅ Index on Project.status, Project.id
✅ Index on AccessRequest(investor, project, status)
✅ No unnecessary database queries
✅ Cached serializer class
✅ Minimal data transfer
```

---

## State Machine: Project Comparison

```
                      START
                        │
                        ↓
        ┌───────────────────────────────┐
        │  Waiting for Project Selection │
        └───────────┬───────────────────┘
                    │
        User selects 1-4 projects
                    │
                    ↓
    ┌────────────────────────────────────┐
    │  Compare Button (Disabled if <2)    │
    └────────────┬──────────────────────┘
                 │
        User clicks Compare
                 │
                 ↓
    ┌────────────────────────────────────┐
    │  Loading Comparison Data           │
    │  GET /api/v1/projects/compare/...  │
    └────────────┬──────────────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
   ERROR                   SUCCESS
     │                       │
     ↓                       ↓
┌─────────────┐   ┌────────────────────┐
│ Error Page  │   │ Comparison Table   │
│ (400/404)   │   │ (Display projects) │
└──────┬──────┘   └────────┬───────────┘
       │                   │
       │        User views restricted field
       │                   │
       │        ┌──────────┴──────────┐
       │        │                     │
       │    has_access           no access
       │    = true                = false
       │        │                     │
       │        ↓                     ↓
       │    Show data          Show "Access Required"
       │        │              + "Request Access" button
       │        │                     │
       │        │        User clicks "Request Access"
       │        │                     │
       │        │                     ↓
       │        │          POST /access-requests/
       │        │                     │
       │        └─────────────┬───────┘
       │                      ↓
       │          Waiting for Admin Approval
       │
       └──────── User navigates away
                            │
                            ↓
                          RESET
```

---

## Summary: Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Compare Action** | `views.py` | Handles GET request, validation |
| **ProjectComparisonSerializer** | `serializers.py` | Applies access control, filters data |
| **get_has_access()** | `serializers.py` | Determines user access level |
| **to_representation()** | `serializers.py` | Masks restricted fields |

