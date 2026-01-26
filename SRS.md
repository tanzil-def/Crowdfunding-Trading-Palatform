# Software Requirements Specification (SRS) - Crowdfunding Trading Platform

**Version:** 1.0  
**Date:** December 23, 2025

## 1. Purpose
This document specifies the software requirements for the Crowdfunding Trading Platform. It defines system features, constraints, and quality expectations for development, testing, and evaluation.

## 2. Scope
The system is a role-based crowdfunding platform:
- **Developers** create projects and submit for approval.
- **Investors** browse projects, request access to restricted details, and invest using a share-based model.
- **Admins** approve projects, manage restricted access, monitor investments, and maintain auditability.

The MVP includes authentication, project workflow, restricted access control, share investing, sandbox payment, favorites, comparator, 3D viewer, notifications, dashboards for Developers and Investors, and an admin panel with audit logging.

## 2.5 Glossary & Key Definitions

**SHARES**
- Unit of ownership in a project.
- Each share represents (Total Project Value ÷ Total Shares).
- Shares are indivisible (cannot purchase fractional shares).
- Shares sold cannot exceed total shares defined.

**RESTRICTED FIELDS**
- Project data fields requiring explicit access approval.
- Examples: financial projections, technical specifications, legal documents.
- Access is per-project, not global.
- Access can be PENDING, APPROVED, REJECTED, or REVOKED.

**SANDBOX PAYMENT**
- Test payment gateway for MVP.
- No real money transactions.
- Simulates success/failure scenarios.
- Must be replaced with production gateway before launch.

**ACCESS APPROVAL**
- Admin-controlled permission to view restricted project data.
- Requires verified email.
- Can be revoked at any time.
- Revocation takes immediate effect.

**SHARE PRICE**
- Calculated value: Total Project Value ÷ Total Shares.
- Fixed at project creation.
- Cannot be changed after approval.
- Used to calculate investment amount.

**AUDIT LOG**
- Immutable record of critical system actions.
- Contains: actor, action, timestamp, entity, metadata.
- Cannot be deleted or modified.
- Retention: minimum 7 years (financial compliance).

**FUNDING PERCENTAGE**
- (Shares Sold ÷ Total Shares) × 100.
- Real-time calculated field.
- Used to track project progress.

## 3. System Overview

### 3.1 User Roles
- **Admin**: Approvals, access control, governance, logs.
- **Project Developer**: Creates projects, monitors funding via dashboard.
- **Investor**: Browses, compares, favorites, requests access, investors, monitors portfolio via dashboard.

### 3.2 Operating Environment
- Web application accessible via modern browsers (Chrome, Firefox).
- Secure backend server with HTTPS communication.
- Dashboard-based UI for Admin, Developer, and Investor.
- Comparator presented as a side-by-side table.
- 3D viewer supports rotating, zoom, and reset controls.

### 3.3 Assumptions and Constraints
**Assumptions:**
- Email verification is required for investing and restricted access requests.
- Dashboard metrics are derived from stored transactions.
- Email delivery is reliable.

**Constraints:**
- Payment is sandbox-only in MVP.
- Restricted data must be enforced at API level, not only UI.
- Share allocation must be atomic to prevent overselling under concurrency.
- Uploaded media must follow configured size and format limits.

## 4. User Stories

### 4.1 Authentication
- As a user, I want to register as an Investor or Developer so I can access the correct features.
- As a user, I want to verify my email so I can securely access protected actions.
- As a user, I want to log in and log out so my account stays secure.
- As a user, I want to reset my password so I can recover access.

### 4.2 Developer Project Management
- As a Developer, I want to create a project so investors can invest after approval.
- As a Developer, I want to upload media and optional 3D assets to showcase the project.
- As a Developer, I want to submit my project for admin review so it can go live.
- As a Developer, I want controlled edit rules based on project status, so the workflow is managed.
- As a Developer, I want a dashboard so I can track investors, secured amount, and funding progress.

### 4.3 Admin Project Review
- As an Admin, I want a review queue so I can process projects efficiently.
- As an Admin, I want to approve, reject, or request changes, so only valid projects go live.
- As an Admin, I want decisions and access-control actions logged, so actions are traceable.

### 4.4 Investor Discovery and Tools
- As an Investor, I want to browse approved projects so I can find opportunities.
- As an Investor, I want to search and filter projects so I can find relevant options.
- As an Investor, I want to do my favorite projects so I can revisit them easily.
- As an Investor, I want to compare projects side by side so I can decide faster.
- As an Investor, I want a dashboard so I can track investments, project progress, and portfolio summary.

### 4.5 Restricted Access
- As an Investor, I want to request access to restricted project details so I can evaluate deeper information.
- As an Admin, I want to approve, reject, or revoke access, so sensitive data remains controlled.

### 4.6 Investment and Payment
- As an Investor, I want to buy shares so I can invest in projects.
- As an Admin, I want payment and investment logs so I can audit transactions.

### 4.7 3D Viewer
- As an Investor, I want to view 3D project content so I can understand visuals better.
- As an Admin, I want file limits enforced, so the platform remains stable.

### 4.8 Notifications
- As an Admin, I want notifications for submissions and access requests so I can respond quickly.
- As a Developer, I want notifications about approval results so I can act.
- As an Investor, I want notifications about access and payment, so I stay updated.

### 4.9 Admin Panel and Logs
- As an Admin, I want a management panel so I can govern users, projects, and access requests.
- As an Admin, I want audit logs, so critical actions are traceable and reviewable.

## 5. Functional Requirements

### 5.1 Authentication and Account Management
- The system shall allow users to register using email and passwords.
- The system shall require email verification.
- The system shall provide login and logout.
- The system shall provide password reset via email.
- The system shall enforce role-based access control for Admin, Developer, and Investor.
- Unverified investors shall not be able to invest or request restricted access.
- Unauthorized users shall not be able to access restricted APIs or data.

#### 5.1.1 Complete RBAC Permission Matrix

| Action | Admin | Developer | Investor |
| :--- | :---: | :---: | :---: |
| **USER MANAGEMENT** | | | |
| - View all users | ✅ | ❌ | ❌ |
| - Create admin user | ✅ | ❌ | ❌ |
| - Deactivate user | ✅ | ❌ | ❌ |
| - Verify email manually | ✅ | ❌ | ❌ |
| - Change user role | ✅ | ❌ | ❌ |
| **PROJECT MANAGEMENT** | | | |
| - Create project | ❌ | ✅ | ❌ |
| - Edit own project | ❌ | ✅* | ❌ |
| - Submit for review | ❌ | ✅ | ❌ |
| - Approve/Reject | ✅ | ❌ | ❌ |
| - View all projects | ✅ | ❌ | ❌ |
| - Archive project | ✅ | ❌ | ❌ |
| - View public projects | ✅ | ✅ | ✅ |
| - View restricted fields | ✅ | ✅** | 🔐*** |
| **MEDIA MANAGEMENT** | | | |
| - Upload media | ❌ | ✅* | ❌ |
| - Delete media | ✅ | ✅* | ❌ |
| - Update media settings | ✅ | ✅* | ❌ |
| - View restricted media | ✅ | ✅** | 🔐*** |
| **INVESTMENT** | | | |
| - Initiate investment | ❌ | ❌ | ✅**** |
| - View own investments | ❌ | ❌ | ✅ |
| - View project investors | ✅ | ✅** | ❌ |
| - View all transactions | ✅ | ❌ | ❌ |
| **ACCESS REQUESTS** | | | |
| - Create request | ❌ | ❌ | ✅**** |
| - Approve/Reject/Revoke| ✅ | ❌ | ❌ |
| - View all requests | ✅ | ❌ | ❌ |
| - View own requests | ❌ | ❌ | ✅ |
| - View project requests | ✅ | ✅** | ❌ |
| **NOTIFICATIONS** | | | |
| - View own notifications| ✅ | ✅ | ✅ |
| - Mark as read | ✅ | ✅ | ✅ |
| - Configure preferences | ✅ | ✅ | ✅ |
| **AUDIT LOGS** | | | |
| - View audit logs | ✅ | ❌ | ❌ |
| - Export audit logs | ✅ | ❌ | ❌ |
| **DASHBOARDS** | | | |
| - View admin dashboard | ✅ | ❌ | ❌ |
| - View dev dashboard | ❌ | ✅ | ❌ |
| - View investor dashboard| ❌ | ❌ | ✅ |

**LEGEND:**
✅ = Allowed, ❌ = Denied, 🔐 = Conditional (requires approval)
* = Only for own projects
** = Only for own projects
*** = Only if access approved
**** = Requires verified email

### 5.2 Project Requirements (Developer)
- The system shall allow Developers to create projects with required fields.
- The system shall support states: Draft, Pending Review, Approved, Rejected, Needs Changes, Archived.
- Editing is only allowed in DRAFT or NEEDS_CHANGES states.

#### 5.2.1 Project State Machine

| Current State | Allowed Action | Actor | Next State(s) |
| :--- | :--- | :--- | :--- |
| **DRAFT** | Edit | Developer | DRAFT |
| **DRAFT** | Submit for Review | Developer | PENDING |
| **DRAFT** | Delete | Developer | (deleted) |
| **PENDING** | Approve | Admin | APPROVED |
| **PENDING** | Reject | Admin | REJECTED |
| **PENDING** | Request Changes | Admin | NEEDS_CHANGES |
| **APPROVED** | Archive | Admin | ARCHIVED |
| **APPROVED** | (no edits allowed) | Developer | APPROVED |
| **REJECTED** | (no actions) | Developer | (terminal state) |
| **NEEDS_CHANGES** | Edit | Developer | NEEDS_CHANGES |
| **NEEDS_CHANGES** | Resubmit | Developer | PENDING |
| **ARCHIVED** | (no actions) | Anyone | (terminal state) |

### 5.7 Restricted Data Access Control
- Verified investors shall be able to request access.
- Admin shall be able to approve, reject, or revoke access.

#### 5.7.1 Access Request State Machine

| State | Action | Actor | Next State |
| :--- | :---: | :---: | :--- |
| **PENDING** | Approve | Admin | APPROVED |
| **PENDING** | Reject | Admin | REJECTED |
| **APPROVED** | Revoke | Admin | REVOKED |
| **REJECTED** | Request Again | Investor | PENDING (new) |
| **REVOKED** | (no actions) | - | (terminal) |

### 5.8 Share-Based Investment and Payment (Sandbox)
- Calculations based on Total Project Value and Total Shares.
- Overselling strictly prohibited (atomic transactions).

#### 5.8.1 Payment Transaction State Machine

| State | Trigger | Next State | Side Effects |
| :--- | :--- | :--- | :--- |
| **INITIATED** | Investor submits | PROCESSING | Lock shares |
| **PROCESSING** | Gateway confirms | SUCCESS | Allocate shares |
| **PROCESSING** | Gateway fails | FAILED | Release lock |
| **SUCCESS** | (terminal) | - | Update dashboard |
| **FAILED** | User retries | INITIATED | New transaction |
| **FAILED** | Timeout | EXPIRED | Release lock |

### 5.13 User Management (Admin)
- Admin shall be able to list all users, view details, deactivate, and manually verify.

### 5.14 Developer Investor Visibility
- Developer shall be able to view masked investor list for their projects.

### 5.15 Enhanced Admin Project Management
- Admin shall be able to list all projects, archive, and view platform statistics.

### 5.16 Media Management
- Developer shall be able to delete/toggle restriction on media (only in Draft/Needs Changes).

### 5.17 Notification Enhancements
- Unread count, mark all read, and preferences.

### 5.18 Project Categories
- List available categories with project counts.

### 5.19 Developer Access Request Visibility
- Developer shall be able to view access requests for their projects.

## 6. Non-Functional Requirements

### 6.1 Security Requirements (DETAILED)
- Password Policy: Min 8 chars, uppercase, lowercase, number, special.
- JWT Management: 15m access, 7d refresh token.
- API Rate Limiting: 5/min for auth, 1000/hr general.
- Webhook Validation: HMAC-SHA256 signature verification.

### 6.2 Performance Requirements (SLA)
- Response Times (p50): List < 200ms, Details < 100ms, Initiate < 500ms.
- Throughput: 100 concurrent users (MVP).
- Real-time: Dashboard updates < 30s.

## 6.6 Error Handling & API Response Standards

**SUCCESS RESPONSE:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { }
}
```

**ERROR RESPONSE:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": { }
  }
}
```

## 7. Data Requirements

### 7.3 Data Classification & Access Rules
1. **PUBLIC**: title, category, description, etc.
2. **RESTRICTED**: financial_projections, technical_specs (requires approval).
3. **SENSITIVE**: payment IDs, full names (Admin only or Masked).
4. **AUDIT**: Immutable logs (Admin only).

## 8. Testing Requirements

### 8.1 Coverage & Scenarios
- Min 85% code coverage.
- 100% coverage for: Payment, Share allocation, Access control.
- Scenarios: Investor journey, Developer journey, Admin journey.
- Performance: Load testing (100 concurrent users).
