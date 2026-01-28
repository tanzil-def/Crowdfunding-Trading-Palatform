<<<<< HEAD
# Crowdfunding Trading Platform - Backend API

[![Django](https://img.shields.io/badge/Django-4.2.11-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-blue.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

A comprehensive share-based crowdfunding platform backend with role-based access control, project management workflows, investment tracking, and real-time notifications.

## 📋 Table of Contents

- [About Project](#-about-project)
- [Features](#-features)
- [Architecture](#%EF%B8%8F-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#%EF%B8%8F-configuration)
- [Database](#%EF%B8%8F-database)
- [Authentication](#-authentication--authorization)
- [Django Apps](#-django-apps-structure)
- [API Endpoints](#-api-endpoints)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Development](#%EF%B8%8F-development)
- [Code Quality](#-code-quality)
- [Troubleshooting](#-troubleshooting)
- [Deployment](#-deployment)
=======
# 🚀 Crowdfunding Trading Platform

<div align="center">

![Platform Banner](https://via.placeholder.com/800x200/4F46E5/FFFFFF?text=Share-Based+Crowdfunding+Platform)

**Enterprise-grade crowdfunding ecosystem with atomic transactions, role-based access control, and real-time notifications**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2.11-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.x-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=JSON%20web%20tokens&logoColor=white)](https://jwt.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[Live Demo](#) · [Documentation](#-api-documentation) · [Report Bug](https://github.com/yourusername/crowdfunding-platform/issues) · [Request Feature](https://github.com/yourusername/crowdfunding-platform/issues)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Security & Best Practices](#-security--best-practices)
>>>>>>> main
- [Contributing](#-contributing)

---

<<<<<<< HEAD
## 📖 About Project

The Crowdfunding Trading Platform backend is a Django REST Framework-based API that enables developers to raise funds for their projects through share-based crowdfunding. The platform features:

- **Role-Based Access Control**: Admin, Developer, and Investor roles with granular permissions
- **Project Management**: Complete CRUD operations with admin approval workflow
- **Share-Based Investment System**: Atomic share allocation with wallet management
- **Access Control**: Restricted content with investor request/approval system
- **Real-Time Notifications**: WebSocket-based notifications for all user actions
- **Audit Logging**: Complete audit trail for governance and compliance
- **REST API**: Fully documented OpenAPI/Swagger endpoints

---

## ✨ Features

### Authentication & Authorization

| Feature | Description |
|---------|-------------|
| JWT Authentication | SimpleJWT with access/refresh tokens |
| Google OAuth | Social authentication support |
| Email Verification | Required for investment actions |
| Password Reset | Secure token-based password recovery |
| Role-Based Access | Admin, Developer, Investor permissions |

### Project Management

| Feature | Description |
|---------|-------------|
| CRUD Operations | Create, read, update, delete projects |
| Approval Workflow | Pending → Approved/Rejected/Needs Changes |
| Media Upload | Images, videos, 3D models support |
| Restricted Fields | Developer-defined access-controlled content |
| Project Categories | Organized by industry/type |

### Investment System

| Feature | Description |
|---------|-------------|
| Share Purchase | Atomic share allocation with locking |
| Payment Integration | Payment gateway callback handling |
| Wallet Management | Track balances and transactions |
| Portfolio Summary | Investor dashboard analytics |
| Transaction History | Complete audit trail |

### Access Control

| Feature | Description |
|---------|-------------|
| Access Requests | Investors request access to restricted content |
| Admin Approval | Approve/reject/revoke access |
| Dynamic Filtering | Automatic content restriction based on access |

### Governance & Monitoring

| Feature | Description |
|---------|-------------|
| Audit Logging | All admin actions logged with metadata |
| Real-Time Notifications | WebSocket notifications for events |
| User Verification | Admin-controlled email verification |
| Activity Tracking | Complete user action history |

### API Features

| Feature | Description |
|---------|-------------|
| OpenAPI Schema | Auto-generated API documentation |
| Swagger UI | Interactive API testing interface |
| Pagination | Configurable page sizes |
| Filtering | Query parameter-based filtering |
| Ordering | Sort by multiple fields |
| Search | Full-text search on relevant fields |

---

## 🏗️ Architecture

### Technology Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | Django 4.2.11 | Web framework |
| **API** | Django REST Framework | REST API development |
| **Database** | PostgreSQL 14+ | Relational database |
| **Authentication** | SimpleJWT | JWT token management |
| **WebSockets** | Django Channels + Daphne | Real-time notifications |
| **API Docs** | drf-spectacular | OpenAPI schema generation |
| **CORS** | django-cors-headers | Cross-origin requests |
| **Filtering** | django-filter | Query filtering |
| **Testing** | pytest | Unit and integration tests |

### System Design

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│  (React Frontend, Mobile Apps, Third-party Integrations) │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTP/HTTPS + WebSocket
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   API Gateway Layer                      │
│         (CORS, Authentication, Rate Limiting)            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Django Application                      │
│  ┌────────────┬────────────┬────────────┬────────────┐  │
│  │   Users    │  Projects  │Investments │   Audit    │  │
│  │    App     │    App     │    App     │    App     │  │
│  └────────────┴────────────┴────────────┴────────────┘  │
│  ┌────────────┬────────────┬────────────┬────────────┐  │
│  │   Access   │Notifications│ Dashboard  │ Favorites  │  │
│  │  Requests  │    App     │    App     │    App     │  │
│  └────────────┴────────────┴────────────┴────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  PostgreSQL Database                     │
│     (Users, Projects, Investments, Audit Logs, etc.)     │
└──────────────────────────────────────────────────────────┘
=======
## 🎯 Overview

A production-ready **share-based crowdfunding platform** that enables developers to raise capital by selling project shares to verified investors. Built with Django REST Framework, this platform implements enterprise-grade patterns including atomic transactions, comprehensive audit trails, and granular access control.

### 🎪 Live Demo

> **Demo Credentials:**
> - Admin: `admin@platform.com` / `admin123`
> - Developer: `dev@platform.com` / `dev123`
> - Investor: `investor@platform.com` / `invest123`

🔗 **API Playground:** [https://api.crowdfunding.io/swagger/](https://api.crowdfunding.io/swagger/)

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 👥 Multi-Role System
- **Admins**: Project approval, user management
- **Developers**: Project creation, analytics
- **Investors**: Share purchases, portfolio tracking

### 🔐 Enterprise Security
- JWT authentication with token refresh
- Email verification enforcement
- OAuth 2.0 (Google) integration
- Row-level permissions

</td>
<td width="50%">

### 💰 Share-Based Funding
- Atomic share allocation (prevents overselling)
- Idempotent payment processing
- Real-time funding progress
- Portfolio analytics

### 📊 Real-Time Features
- Instant notifications
- Live dashboard metrics
- Audit trail logging
- Transaction history

</td>
</tr>
</table>

---

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[React Frontend<br/>Vite + Redux]
    end
    
    subgraph "API Gateway"
        B[Django REST Framework<br/>JWT Authentication]
        B1[CORS Middleware]
        B2[Rate Limiting]
    end
    
    subgraph "Application Layer"
        C1[Users Module<br/>Auth & Profiles]
        C2[Projects Module<br/>CRUD & Approval]
        C3[Investments Module<br/>Payments & Shares]
        C4[Notifications Module<br/>Real-time Updates]
        C5[Audit Module<br/>Immutable Logs]
    end
    
    subgraph "Data Layer"
        D[(PostgreSQL 16<br/>Primary Database)]
        E[File Storage<br/>Media & Static]
    end
    
    A -->|HTTPS/JSON| B
    B --> B1
    B --> B2
    B --> C1
    B --> C2
    B --> C3
    B --> C4
    B --> C5
    C1 --> D
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C2 --> E
    
    style A fill:#4F46E5,stroke:#4338CA,color:#fff
    style B fill:#10B981,stroke:#059669,color:#fff
    style D fill:#EF4444,stroke:#DC2626,color:#fff
    style E fill:#F59E0B,stroke:#D97706,color:#fff
```

### Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant BL as Business Logic
    participant DB as PostgreSQL
    participant S3 as File Storage
    
    C->>API: POST /api/v1/investments/initiate
    API->>Auth: Verify JWT Token
    Auth-->>API: Token Valid
    
    API->>BL: Process Investment
    
    rect rgb(240, 240, 255)
        Note over BL,DB: Atomic Transaction
        BL->>DB: Lock Project Row (SELECT FOR UPDATE)
        BL->>DB: Check Remaining Shares
        BL->>DB: Create PaymentTransaction
        BL->>DB: Reserve Shares (UPDATE shares_sold)
        BL->>DB: Commit Transaction
    end
    
    BL-->>API: Payment Reference ID
    API-->>C: 201 Created
    
    C->>API: POST /api/v1/investments/payments/callback
    API->>BL: Verify Payment Signature
    
    rect rgb(240, 255, 240)
        Note over BL,DB: Complete Investment
        BL->>DB: Update Payment Status = SUCCESS
        BL->>DB: Create SharePurchase Record
        BL->>DB: Create Notification
        BL->>DB: Create Audit Log
    end
    
    BL-->>API: Investment Confirmed
    API-->>C: 200 OK
```

### Modular Architecture

```mermaid
graph LR
    subgraph "Core Modules"
        A[Users<br/>Authentication]
        B[Projects<br/>Management]
        C[Investments<br/>Payments]
    end
    
    subgraph "Supporting Modules"
        D[Notifications<br/>Alerts]
        E[Audit<br/>Logging]
        F[Favorites<br/>Bookmarks]
        G[Access Requests<br/>Permissions]
        H[Dashboard<br/>Analytics]
    end
    
    A -.->|Authenticates| B
    A -.->|Authenticates| C
    B -->|Triggers| D
    C -->|Triggers| D
    B -->|Logs| E
    C -->|Logs| E
    B <-->|References| F
    B <-->|Manages| G
    A -->|Provides Data| H
    B -->|Provides Data| H
    C -->|Provides Data| H
    
    style A fill:#4F46E5,stroke:#4338CA,color:#fff
    style B fill:#10B981,stroke:#059669,color:#fff
    style C fill:#EF4444,stroke:#DC2626,color:#fff
    style D fill:#F59E0B,stroke:#D97706,color:#fff
    style E fill:#8B5CF6,stroke:#7C3AED,color:#fff
```

---

## 🛠️ Tech Stack

### Backend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Core programming language |
| **Framework** | Django | 4.2.11 | Web application framework |
| **API** | Django REST Framework | 3.x | RESTful API development |
| **Database** | PostgreSQL | 16 | Primary relational database |
| **Authentication** | SimpleJWT | 2.7.0 | JWT token management |
| **Documentation** | drf-spectacular | 0.27.0 | OpenAPI 3.0 schema |
| **CORS** | django-cors-headers | 4.3.1 | Cross-origin requests |
| **Filtering** | django-filter | 23.5 | Query filtering |
| **Image Processing** | Pillow | 10.2.0 | Image handling |
| **Environment** | python-decouple | 3.8 | Configuration management |

### Infrastructure

```mermaid
graph TB
    subgraph "Production Stack"
        A[Nginx<br/>Reverse Proxy]
        B[Gunicorn<br/>WSGI Server]
        C[Django App<br/>Multiple Workers]
        D[(PostgreSQL<br/>Primary DB)]
        E[Redis<br/>Cache Layer]
        F[Celery<br/>Task Queue]
        G[AWS S3<br/>Media Storage]
    end
    
    A -->|Route Traffic| B
    B -->|Run| C
    C -->|Read/Write| D
    C -->|Cache| E
    C -->|Async Tasks| F
    F -->|Workers| E
    C -->|Upload| G
    
    style A fill:#269636,stroke:#1E7125,color:#fff
    style B fill:#499848,stroke:#3A7A39,color:#fff
    style C fill:#092E20,stroke:#0A1F16,color:#fff
    style D fill:#336791,stroke:#295E7A,color:#fff
    style E fill:#DC382D,stroke:#B82E25,color:#fff
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- pip & virtualenv
- Docker (optional)

### Installation

#### Option 1: Local Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/crowdfunding-platform.git
cd crowdfunding-platform

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your database credentials

# 5. Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE crowdfunding_db;
CREATE USER crowdfunding_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE crowdfunding_db TO crowdfunding_user;
\q

# 6. Run migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Load sample data (optional)
python manage.py loaddata sample_data.json

# 9. Start development server
python manage.py runserver
```

#### Option 2: Docker Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/crowdfunding-platform.git
cd crowdfunding-platform

# 2. Configure environment
cp .env.example .env
# Edit .env if needed

# 3. Build and run containers
docker-compose up --build -d

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser

# 6. Access application
# API: http://localhost:8000
# Swagger: http://localhost:8000/api/swagger/
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/api/v1/health/

# Expected response:
# {"status": "healthy", "database": "connected"}
```

---

## 📡 API Documentation

### Interactive Documentation

| Tool | URL | Purpose |
|------|-----|---------|
| **Swagger UI** | `/api/swagger/` | Interactive API explorer |
| **ReDoc** | `/api/redoc/` | Clean documentation view |
| **OpenAPI Schema** | `/api/schema/` | Machine-readable spec |

### Authentication

All protected endpoints require JWT authentication:

```http
Authorization: Bearer <access_token>
```

**Token Lifecycle:**
- Access Token: 1 hour
- Refresh Token: 7 days

### Core Endpoints

#### 🔐 Authentication (`/api/v1/auth/`)

```http
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/verify-email/
POST /api/v1/auth/password-reset/
POST /api/v1/auth/google/
GET  /api/v1/auth/profile/
```

#### 📊 Projects (`/api/v1/projects/`)

```http
# Public
GET  /api/v1/projects/browse/              # Browse approved projects
GET  /api/v1/projects/{id}/detail/         # View project details

# Developer
POST /api/v1/projects/                     # Create project
GET  /api/v1/projects/my/                  # My projects
PUT  /api/v1/projects/{id}/                # Update project
POST /api/v1/projects/{id}/submit/         # Submit for review
POST /api/v1/projects/{id}/media/          # Upload media

# Admin
GET  /api/v1/projects/admin/pending/       # Pending reviews
POST /api/v1/projects/{id}/approve/        # Approve project
POST /api/v1/projects/{id}/reject/         # Reject project
```

#### 💰 Investments (`/api/v1/investments/`)

```http
POST /api/v1/investments/initiate/         # Initiate purchase
POST /api/v1/investments/payments/callback/ # Payment callback
GET  /api/v1/investments/my/               # My investments
GET  /api/v1/investments/portfolio/summary/ # Portfolio analytics
```

### Sample Requests

#### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investor@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "INVESTOR"
  }'
```

#### Initiate Investment

```bash
curl -X POST http://localhost:8000/api/v1/investments/initiate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "shares_to_purchase": 10
  }'
```

**Response:**
```json
{
  "reference_id": "TXN-20260118-ABC123",
  "amount": 1000.00,
  "payment_url": "https://payment-gateway.com/pay/...",
  "expires_at": "2026-01-18T12:00:00Z"
}
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Project : creates
    User ||--o{ SharePurchase : makes
    User ||--o{ Notification : receives
    User ||--o{ Favorite : has
    User ||--o{ AccessRequest : submits
    
    Project ||--o{ ProjectMedia : contains
    Project ||--o{ SharePurchase : funded_by
    Project ||--o{ PaymentTransaction : receives
    Project ||--o{ Favorite : favorited_by
    Project ||--o{ AccessRequest : for
    
    PaymentTransaction ||--|| SharePurchase : confirms
    
    User {
        uuid id PK
        varchar email UK "Unique email"
        varchar role "ADMIN|DEVELOPER|INVESTOR"
        varchar auth_provider "LOCAL|GOOGLE"
        varchar google_id UK "OAuth ID"
        boolean is_email_verified
        timestamp date_joined
    }
    
    Project {
        uuid id PK
        uuid developer_id FK
        varchar title
        text description
        varchar status "DRAFT|PENDING|APPROVED|REJECTED"
        decimal total_project_value
        int total_shares
        int shares_sold
        timestamp created_at
    }
    
    SharePurchase {
        uuid id PK
        uuid investor_id FK
        uuid project_id FK
        uuid payment_id FK
        int shares_purchased
        decimal price_per_share
        decimal total_amount
        timestamp created_at
    }
    
    PaymentTransaction {
        uuid id PK
        varchar reference_id UK "Idempotency key"
        uuid investor_id FK
        uuid project_id FK
        decimal amount
        varchar status "INITIATED|SUCCESS|FAILED"
        timestamp processed_at
    }
```

### Key Database Constraints

```sql
-- Prevent overselling (CHECK constraint)
ALTER TABLE projects
ADD CONSTRAINT chk_shares_sold 
CHECK (shares_sold <= total_shares);

-- Unique payment reference (Idempotency)
ALTER TABLE payment_transactions
ADD CONSTRAINT unq_reference_id 
UNIQUE (reference_id);

-- Positive share price
ALTER TABLE projects
ADD CONSTRAINT chk_share_price 
CHECK (share_price > 0);
```

### Indexes for Performance

```python
# Composite indexes for common queries
class Project(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at']),  # Browse projects
            models.Index(fields=['developer', 'status']),    # Developer dashboard
            models.Index(fields=['category', 'status']),     # Category filtering
        ]
```

---

## 🔒 Security & Best Practices

### Implemented Security Measures

<table>
<tr>
<td width="50%">

#### 🛡️ Authentication
- ✅ JWT with short expiration (1h)
- ✅ Refresh token rotation
- ✅ Token blacklisting on logout
- ✅ Email verification required
- ✅ Strong password validation

#### 🔐 Authorization
- ✅ Role-based access control
- ✅ Object-level permissions
- ✅ Field-level restrictions
- ✅ Dynamic permission checking

</td>
<td width="50%">

#### ⚛️ Data Integrity
- ✅ Atomic transactions (`@transaction.atomic`)
- ✅ Row-level locking (`select_for_update()`)
- ✅ Idempotent operations
- ✅ Database constraints
- ✅ Input validation (serializers)

#### 📊 Audit & Compliance
- ✅ Immutable audit logs
- ✅ Action traceability
- ✅ Payment history
- ✅ IP address logging

</td>
</tr>
</table>

### Code Quality Patterns

```python
# ✅ GOOD: Atomic share allocation
from django.db import transaction
from django.db.models import F

@transaction.atomic
def purchase_shares(project_id, shares_to_buy):
    # Lock row to prevent race conditions
    project = Project.objects.select_for_update().get(id=project_id)
    
    # Validate availability
    if project.remaining_shares < shares_to_buy:
        raise InsufficientSharesError()
    
    # Atomic update using F() expression
    project.shares_sold = F('shares_sold') + shares_to_buy
    project.save(update_fields=['shares_sold'])
    project.refresh_from_db()
```

```python
# ✅ GOOD: Idempotent payment processing
def process_payment(reference_id, amount):
    # Check for existing transaction
    existing = PaymentTransaction.objects.filter(
        reference_id=reference_id,
        status='SUCCESS'
    ).first()
    
    if existing:
        return existing  # Already processed
    
    # Process new payment
    return PaymentGateway.charge(reference_id, amount)
>>>>>>> main
```

---

## 📁 Project Structure

```
crowdfunding_platform/
<<<<<<< HEAD
├── config/                      # Project configuration
│   ├── __init__.py
│   ├── asgi.py                 # ASGI config for WebSockets
│   ├── settings/               # Split settings
│   │   ├── base.py            # Base settings
│   │   ├── development.py     # Development settings
│   │   └── production.py      # Production settings
│   ├── urls.py                # Main URL configuration
│   └── wsgi.py                # WSGI config
│
├── apps/                       # Django applications
│   ├── users/                 # User management & auth
│   │   ├── models.py          # User, EmailVerificationToken, PasswordResetToken
│   │   ├── serializers.py     # User serializers
│   │   ├── views.py           # Auth endpoints
│   │   ├── services.py        # Business logic
│   │   ├── permissions.py     # Custom permissions
│   │   ├── managers.py        # Custom user manager
│   │   ├── urls.py            # User routes
│   │   ├── admin_urls.py      # Admin user management routes
│   │   └── migrations/
│   │
│   ├── projects/              # Project management
│   │   ├── models.py          # Project, ProjectMedia
│   │   ├── serializers.py     # Project serializers
│   │   ├── views.py           # Project CRUD, admin actions
│   │   ├── services.py        # Project workflow logic
│   │   ├── urls.py            # Project routes
│   │   └── migrations/
│   │
│   ├── investments/           # Investment & wallet system
│   │   ├── models.py          # PaymentTransaction, SharePurchase
│   │   ├── serializers.py     # Investment serializers
│   │   ├── views.py           # Investment endpoints
│   │   ├── services.py        # Payment processing logic
│   │   ├── urls.py            # Investment routes
│   │   └── migrations/
│   │
│   ├── access_requests/       # Content access control
│   │   ├── models.py          # AccessRequest
│   │   ├── serializers.py     # Access request serializers
│   │   ├── views.py           # Access request endpoints
│   │   ├── services.py        # Access control logic
│   │   ├── urls.py            # Access request routes
│   │   └── migrations/
│   │
│   ├── notifications/         # Real-time notifications
│   │   ├── models.py          # Notification, NotificationPreference
│   │   ├── serializers.py     # Notification serializers
│   │   ├── views.py           # Notification endpoints
│   │   ├── services.py        # Notification creation logic
│   │   ├── consumers.py       # WebSocket consumers
│   │   ├── routing.py         # WebSocket routing
│   │   ├── urls.py            # Notification routes
│   │   └── migrations/
│   │
│   ├── audit/                 # Audit logging
│   │   ├── models.py          # AuditLog
│   │   ├── serializers.py     # Audit serializers
│   │   ├── views.py           # Audit log endpoints
│   │   ├── services.py        # Logging utilities
│   │   ├── urls.py            # Audit routes
│   │   └── migrations/
│   │
│   ├── dashboard/             # Analytics & statistics
│   │   ├── views.py           # Dashboard endpoints
│   │   ├── services.py        # Analytics calculations
│   │   ├── serializers.py     # Dashboard serializers
│   │   └── urls.py            # Dashboard routes
│   │
│   └── favorites/             # User favorites
│       ├── models.py          # Favorite
│       ├── serializers.py     # Favorite serializers
│       ├── views.py           # Favorite endpoints
│       ├── urls.py            # Favorite routes
│       └── migrations/
│
├── utils/                     # Shared utilities
│   ├── exceptions.py          # Custom exceptions
│   ├── permissions.py         # Shared permissions
│   ├── renderers.py           # Custom renderers
│   ├── responses.py           # Standardized responses
│   └── validators.py          # Custom validators
│
├── media/                     # User-uploaded files
├── static/                    # Static files
├── templates/                 # Email templates
├── .env                       # Environment variables
├── .gitignore                # Git ignore rules
├── docker-compose.yml        # Docker configuration
├── Dockerfile                # Docker image
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### App Descriptions

| App | Purpose | Key Models |
|-----|---------|-----------|
| **users** | Authentication, user management, roles | User, EmailVerificationToken, PasswordResetToken |
| **projects** | Project CRUD, approval workflow | Project, ProjectMedia |
| **investments** | Share purchases, payments, wallet | PaymentTransaction, SharePurchase |
| **access_requests** | Restricted content access control | AccessRequest |
| **notifications** | Real-time user notifications | Notification, NotificationPreference |
| **audit** | Activity logging for governance | AuditLog |
| **dashboard** | Analytics and statistics | (No models, aggregates data) |
| **favorites** | User project favorites | Favorite |

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.12 or higher
- **PostgreSQL**: 14 or higher
- **pip**: Latest version
- **Git**: For version control
- **Docker** (optional): For containerized deployment

### Installation Steps

#### 1. Clone Repository

```bash
git clone <repository-url>
cd crowdfunding_platform
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required environment variables:**
```env
# Django
DEBUG=True
SECRET_KEY=your-very-strong-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=crowdfunding_db
POSTGRES_USER=crowdfunding_user
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Frontend
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_VERIFICATION_TOKEN_EXPIRY_MINUTES=60

# JWT
SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

#### 5. Setup Database

**Option A: Using Docker**

```bash
# Start PostgreSQL container
docker-compose up -d db

# Wait for database to be ready
sleep 5
```

**Option B: Local PostgreSQL**

```bash
# Create database
createdb crowdfunding_db

# Or using psql
psql -U postgres -c "CREATE DATABASE crowdfunding_db;"
```

#### 6. Run Migrations

```bash
python manage.py migrate
```

#### 7. Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

#### 8. Run Development Server

```bash
python manage.py runserver
```

#### 9. Access API

- **API Base**: http://localhost:8000/api/v1/
- **Swagger UI**: http://localhost:8000/api/swagger/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DEBUG` | ✅ | Debug mode (False in production) | `True` |
| `SECRET_KEY` | ✅ | Django secret key | `long-random-string` |
| `ALLOWED_HOSTS` | ✅ | Allowed host names | `localhost,127.0.0.1` |
| `POSTGRES_DB` | ✅ | Database name | `crowdfunding_db` |
| `POSTGRES_USER` | ✅ | Database user | `crowdfunding_user` |
| `POSTGRES_PASSWORD` | ✅ | Database password | `secure-password` |
| `POSTGRES_HOST` | ✅ | Database host | `localhost` or `db` |
| `POSTGRES_PORT` | ✅ | Database port | `5432` |
| `FRONTEND_URL` | ✅ | Frontend application URL | `http://localhost:3000` |
| `CORS_ALLOWED_ORIGINS` | ✅ | CORS allowed origins | `http://localhost:3000` |
| `EMAIL_BACKEND` | ❌ | Email backend class | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | ❌ | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | ❌ | SMTP port | `587` |
| `EMAIL_HOST_USER` | ❌ | Email username | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | ❌ | Email password | `app-password` |
| `SITE_DOMAIN` | ❌ | Site domain for emails | `127.0.0.1:8000` |

### Settings Structure

The project uses split settings for different environments:

```python
config/settings/
├── base.py          # Common settings
├── development.py   # Development-specific
└── production.py    # Production-specific
```

To use specific settings:

```bash
# Development (default)
python manage.py runserver

# Production
python manage.py runserver --settings=config.settings.production
```

---

## 🗄️ Database

### Models Overview

| Model | App | Purpose | Key Fields |
|-------|-----|---------|-----------|
| `User` | users | Custom user model | email, role, is_email_verified, is_active |
| `EmailVerificationToken` | users | Email verification | user, token, expires_at |
| `PasswordResetToken` | users | Password reset | user, token, expires_at |
| `Project` | projects | Crowdfunding projects | title, status, total_project_value, total_shares, share_price |
| `ProjectMedia` | projects | Project media files | project, media_type, file_url |
| `PaymentTransaction` | investments | Payment tracking | investor, project, amount, status, reference_id |
| `SharePurchase` | investments | Share ownership | investor, project, shares_purchased, price_per_share |
| `AccessRequest` | access_requests | Content access | investor, project, status, decided_by |
| `Notification` | notifications | User notifications | user, notification_type, message, is_read |
| `AuditLog` | audit | Activity logging | actor, action, entity_type, entity_id, metadata |
| `Favorite` | favorites | User favorites | user, project |

### Database Migrations

```bash
# Create new migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback to specific migration
python manage.py migrate <app_name> <migration_number>

# Show SQL for migration
python manage.py sqlmigrate <app_name> <migration_number>
```

### Database Management

```bash
# Enter database shell
python manage.py dbshell

# Dump data to JSON
python manage.py dumpdata > backup.json

# Load data from JSON
python manage.py loaddata backup.json

# Flush database (WARNING: deletes all data)
python manage.py flush
```

---

## 🔐 Authentication & Authorization

### JWT Authentication Flow

```
1. User logs in with email/password
   ↓
2. Server validates credentials
   ↓
3. Server generates access_token & refresh_token
   ↓
4. Client stores tokens
   ↓
5. Client includes access_token in Authorization header
   ↓
6. Server validates token on each request
   ↓
7. When access_token expires, use refresh_token to get new one
```

### Login Endpoint

```bash
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### Using Tokens

```bash
# Include access token in Authorization header
curl -X GET http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token

```bash
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **ADMIN** | • Manage all users<br>• Approve/reject projects<br>• View all transactions<br>• Manage access requests<br>• View audit logs |
| **DEVELOPER** | • Create projects<br>• Edit own projects<br>• View project analytics<br>• Respond to investor questions |
| **INVESTOR** | • Browse approved projects<br>• Purchase shares<br>• Request access to restricted content<br>• View portfolio |

---

## 📦 Django Apps Structure

### Users App

**Purpose**: User authentication, profiles, and role management

**Models**:
- `User`: Custom user model with email as username, role field (ADMIN/DEVELOPER/INVESTOR)
- `EmailVerificationToken`: Token-based email verification
- `PasswordResetToken`: Secure password reset tokens

**Key Endpoints**:
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/login/` - Login with email/password
- `POST /api/v1/auth/logout/` - Logout (blacklist refresh token)
- `POST /api/v1/auth/verify-email/` - Verify email with token
- `POST /api/v1/auth/password-reset/` - Request password reset
- `POST /api/v1/auth/password-reset-confirm/` - Confirm password reset
- `GET /api/v1/auth/profile/` - Get user profile
- `POST /api/v1/auth/google/` - Google OAuth login

---

### Projects App

**Purpose**: Project management, CRUD operations, and approval workflow

**Models**:
- `Project`: Main project model with status workflow (DRAFT → PENDING → APPROVED/REJECTED/NEEDS_CHANGES)
- `ProjectMedia`: Images, videos, 3D models associated with projects

**Key Endpoints**:
- `GET /api/v1/projects/` - List all projects
- `POST /api/v1/projects/` - Create new project (Developer only)
- `GET /api/v1/projects/{id}/` - Get project details
- `PUT /api/v1/projects/{id}/` - Update project (Developer only)
- `DELETE /api/v1/projects/{id}/` - Delete project (Developer only)
- `POST /api/v1/projects/{id}/submit/` - Submit for admin review
- `GET /api/v1/projects/browse/` - Browse approved projects (Public)
- `POST /api/v1/projects/admin/projects/{id}/approve/` - Approve project (Admin only)
- `POST /api/v1/projects/admin/projects/{id}/reject/` - Reject project (Admin only)

---

### Investments App

**Purpose**: Share purchases, payment processing, and wallet management

**Models**:
- `PaymentTransaction`: Tracks all payment attempts (INITIATED → SUCCESS/FAILED)
- `SharePurchase`: Records successful share purchases

**Key Endpoints**:
- `POST /api/v1/investments/initiate/` - Initiate investment
- `POST /api/v1/investments/payments/callback/` - Payment gateway callback
- `GET /api/v1/investments/my/` - List my investments
- `GET /api/v1/investments/{id}/` - Get investment details
- `GET /api/v1/investments/portfolio/summary/` - Portfolio summary
- `GET /api/v1/investments/admin/transactions/` - All transactions (Admin only)

---

### Access Requests App

**Purpose**: Control access to restricted project content

**Models**:
- `AccessRequest`: Investor requests to view restricted project data (PENDING → APPROVED/REJECTED/REVOKED)

**Key Endpoints**:
- `POST /api/v1/access-requests/` - Create access request
- `GET /api/v1/access-requests/my/` - My access requests
- `GET /api/v1/access-requests/admin/` - All requests (Admin only)
- `POST /api/v1/access-requests/admin/{id}/approve/` - Approve request (Admin only)
- `POST /api/v1/access-requests/admin/{id}/reject/` - Reject request (Admin only)
- `POST /api/v1/access-requests/admin/{id}/revoke/` - Revoke access (Admin only)

---

### Notifications App

**Purpose**: Real-time user notifications via WebSocket

**Models**:
- `Notification`: User notifications with type, message, and read status
- `NotificationPreference`: User notification preferences

**Key Endpoints**:
- `GET /api/v1/notifications/` - List notifications
- `PATCH /api/v1/notifications/{id}/read/` - Mark as read
- `POST /api/v1/notifications/mark-all-read/` - Mark all as read
- `GET /api/v1/notifications/unread-count/` - Get unread count
- `GET /api/v1/notifications/preferences/` - Get preferences
- `PUT /api/v1/notifications/preferences/` - Update preferences

**WebSocket**: `ws://localhost:8000/ws/notifications/`

---

### Audit App

**Purpose**: Activity logging for governance and compliance

**Models**:
- `AuditLog`: Immutable log of all admin actions with actor, action, entity, and metadata

**Key Endpoints**:
- `GET /api/v1/audit/admin/audit-logs/` - View audit logs (Admin only)

---

## 🌐 API Endpoints

### Complete Endpoint List

#### Authentication & Users

```
POST   /api/v1/auth/register/                    - Register user
POST   /api/v1/auth/login/                       - Login
POST   /api/v1/auth/logout/                      - Logout
POST   /api/v1/auth/verify-email/                - Verify email
POST   /api/v1/auth/password-reset/              - Request password reset
POST   /api/v1/auth/password-reset-confirm/      - Confirm password reset
POST   /api/v1/auth/google/                      - Google OAuth
GET    /api/v1/auth/profile/                     - Get profile
POST   /api/v1/auth/token/refresh/               - Refresh JWT token
```

#### Projects

```
GET    /api/v1/projects/                         - List projects
POST   /api/v1/projects/                         - Create project
GET    /api/v1/projects/{id}/                    - Get project
PUT    /api/v1/projects/{id}/                    - Update project
DELETE /api/v1/projects/{id}/                    - Delete project
POST   /api/v1/projects/{id}/submit/             - Submit for review
GET    /api/v1/projects/browse/                  - Browse approved
POST   /api/v1/projects/{id}/media/              - Upload media
```

#### Admin - Users

```
GET    /api/v1/admin/users/                      - List all users
GET    /api/v1/admin/users/{id}/                 - Get user
PUT    /api/v1/admin/users/{id}/                 - Update user
PATCH  /api/v1/admin/users/{id}/                 - Partial update
DELETE /api/v1/admin/users/{id}/                 - Deactivate user
POST   /api/v1/admin/users/{id}/verify-email/    - Verify email
POST   /api/v1/admin/users/{id}/deactivate/      - Deactivate user
```

#### Admin - Projects

```
GET    /api/v1/projects/admin/projects/pending/           - Pending projects
POST   /api/v1/projects/admin/projects/{id}/approve/      - Approve
POST   /api/v1/projects/admin/projects/{id}/reject/       - Reject
POST   /api/v1/projects/admin/projects/{id}/request-changes/ - Request changes
POST   /api/v1/projects/admin/projects/{id}/archive/      - Archive
GET    /api/v1/projects/admin/projects/statistics/        - Platform stats
```

#### Investments

```
POST   /api/v1/investments/initiate/                      - Initiate investment
GET    /api/v1/investments/my/                            - My investments
GET    /api/v1/investments/{id}/                          - Investment details
GET    /api/v1/investments/portfolio/summary/             - Portfolio summary
POST   /api/v1/investments/payments/callback/             - Payment callback
GET    /api/v1/investments/admin/transactions/            - All transactions (Admin)
GET    /api/v1/investments/admin/transactions/{id}/       - Transaction detail (Admin)
```

#### Access Requests

```
POST   /api/v1/access-requests/                           - Create request
GET    /api/v1/access-requests/my/                        - My requests
GET    /api/v1/access-requests/admin/                     - All requests (Admin)
POST   /api/v1/access-requests/admin/{id}/approve/        - Approve (Admin)
POST   /api/v1/access-requests/admin/{id}/reject/         - Reject (Admin)
POST   /api/v1/access-requests/admin/{id}/revoke/         - Revoke (Admin)
```

#### Notifications

```
GET    /api/v1/notifications/                             - List notifications
PATCH  /api/v1/notifications/{id}/read/                   - Mark as read
POST   /api/v1/notifications/mark-all-read/               - Mark all read
GET    /api/v1/notifications/unread-count/                - Unread count
GET    /api/v1/notifications/preferences/                 - Get preferences
PUT    /api/v1/notifications/preferences/                 - Update preferences
```

#### Audit Logs

```
GET    /api/v1/audit/admin/audit-logs/                    - View logs (Admin)
```

#### Favorites

```
POST   /api/v1/favorites/                                 - Add favorite
GET    /api/v1/favorites/                                 - List favorites
DELETE /api/v1/favorites/{id}/                            - Remove favorite
```

#### Dashboard

```
GET    /api/v1/dashboard/admin/                           - Admin dashboard (Admin)
GET    /api/v1/dashboard/developer/                       - Developer dashboard (Developer)
GET    /api/v1/dashboard/investor/                        - Investor dashboard (Investor)
```

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/swagger/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Generate OpenAPI Schema

```bash
# Generate schema file
python manage.py spectacular --file schema.yml

# Validate schema
python manage.py spectacular --validate
```

---

## 🧪 Testing

### Test Structure

```
tests/
├── test_users.py              - User authentication tests
├── test_projects.py           - Project management tests
├── test_investments.py        - Investment system tests
├── test_access_requests.py    - Access control tests
├── test_notifications.py      - Notification tests
├── test_audit.py              - Audit logging tests
├── conftest.py                - Pytest fixtures
└── factories.py               - Test data factories
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_user_registration

# Verbose output
pytest -v

# Show print statements
pytest -s

# Run tests matching pattern
pytest -k "test_create"

# Run with parallel execution
pytest -n auto
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=apps --cov-report=html

# View report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### Test Categories

- **Unit Tests**: Models, serializers, utilities
- **Integration Tests**: API endpoints, workflows
- **Permission Tests**: Role-based access control
- **Workflow Tests**: Project approval, investment flow

---

## 🛠️ Development

### Common Commands

```bash
# Start development server
python manage.py runserver

# Start with specific port
python manage.py runserver 8080

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Enter Django shell
python manage.py shell

# Enter Django shell with iPython
python manage.py shell -i ipython

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check

# Show URLs
python manage.py show_urls

# Flush database (WARNING: deletes all data)
python manage.py flush
```

### Development Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **Black** | Code formatting | `black .` |
| **isort** | Import sorting | `isort .` |
| **Flake8** | Style checking | `flake8` |
| **Mypy** | Type checking | `mypy .` |
| **Pytest** | Testing | `pytest` |
| **Coverage** | Code coverage | `pytest --cov` |

---

## 📊 Code Quality

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .

# Run all checks
black . && isort . && flake8 && mypy .
```

### Code Style Guidelines

- Follow **PEP 8** style guide
- Max line length: **88 characters** (Black default)
- Use **type hints** for function parameters and return values
- Write **docstrings** for all public functions and classes
- Keep functions **small and focused** (single responsibility)
- Use **meaningful variable names**

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## ❓ Troubleshooting

### Common Issues

#### ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'module_name'`

**Solution**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

#### Database Connection Error

**Problem**: `django.db.utils.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker ps  # if using Docker
# or
sudo systemctl status postgresql  # if local

# Start database
docker-compose up -d db  # if using Docker
# or
sudo systemctl start postgresql  # if local

# Check DATABASE_URL in .env
```

---

#### CORS Error

**Problem**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**:
```bash
# Add frontend URL to .env
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Restart server
python manage.py runserver
```

---

#### Migration Error

**Problem**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution**:
```bash
# Option 1: Run sync
python manage.py migrate --run-syncdb

# Option 2: Fake migrations (if database is correct)
python manage.py migrate --fake

# Option 3: Reset migrations (WARNING: data loss)
python manage.py migrate <app_name> zero
python manage.py migrate
```

---

#### 401 Unauthorized

**Problem**: API returns 401 even with valid token

**Solution**:
```bash
# Check token expiration
# Tokens expire after 60 minutes by default

# Refresh token
POST /api/v1/auth/token/refresh/
{
  "refresh": "<refresh_token>"
}

# Check SIMPLE_JWT settings in .env
```

---

#### Import Error

**Problem**: `ImportError: cannot import name 'X' from 'Y'`

**Solution**:
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Ensure virtual environment is activated
which python  # should point to .venv/bin/python

# Reinstall package
pip uninstall <package>
pip install <package>
```

---

## 🔄 Deployment

### Pre-deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Update `SECRET_KEY` with strong random value
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Configure production database (`DATABASE_URL`)
- [ ] Set up email backend (SMTP settings)
- [ ] Configure static files serving
- [ ] Set up media files storage
- [ ] Run all tests: `pytest`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Set up monitoring and logging
- [ ] Configure HTTPS/SSL
- [ ] Set up backup strategy

### Production Settings

```python
# config/settings/production.py

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Docker Deployment

```bash
# Build image
docker build -t crowdfunding-backend .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
=======
├── 📦 apps/                    # Django applications
│   ├── 🔐 users/               # Authentication & profiles
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── services.py
│   ├── 📊 projects/            # Project management
│   ├── 💰 investments/         # Payment processing
│   ├── 🔔 notifications/       # Real-time alerts
│   ├── 📋 audit/               # Logging system
│   ├── ⭐ favorites/           # Bookmarks
│   ├── 🔑 access_requests/    # Permission requests
│   └── 📈 dashboard/           # Analytics
│
├── ⚙️ config/                  # Django configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   └── wsgi.py
│
├── 🛠️ utils/                   # Shared utilities
│   ├── pagination.py
│   ├── permissions.py
│   └── validators.py
│
├── 📄 media/                   # User uploads (gitignored)
├── 📄 static/                  # Static files
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📋 requirements.txt
└── 📖 README.md
>>>>>>> main
```

---

## 🤝 Contributing

<<<<<<< HEAD
### How to Contribute

1. **Fork** the repository
2. Create a **feature branch**: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Write or update **tests**
5. Run quality checks: `black . && isort . && flake8 && pytest`
6. **Commit** your changes: `git commit -m 'Add amazing feature'`
7. **Push** to the branch: `git push origin feature/amazing-feature`
8. Open a **Pull Request**

### Code Standards

- Follow **PEP 8** style guide
- Write **docstrings** for all public functions
- Add **type hints** to function signatures
- Write **tests** for new features
- Update **documentation** as needed
- Keep commits **atomic** and **descriptive**

### Pull Request Guidelines

- Provide clear description of changes
- Reference related issues
- Include screenshots for UI changes
- Ensure all tests pass
- Update README if needed

---

## 📞 Support & Contact

### Need Help?

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [API Documentation](#-api-documentation)
3. Check test examples in `tests/` directory
4. Open an issue on GitHub

### Resources

- **API Documentation**: http://localhost:8000/api/swagger/
- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
=======
We welcome contributions! Please follow these steps:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit** your changes:
   ```bash
   git commit -m 'feat: add amazing feature'
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open** a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user portfolio analytics
fix: resolve race condition in share allocation
docs: update API documentation
refactor: improve payment processing service
test: add investment flow integration tests
```

### Code Standards

- ✅ Follow PEP 8 style guide
- ✅ Write docstrings for all public functions
- ✅ Add unit tests (coverage > 80%)
- ✅ Update API documentation
- ✅ Run linters before committing:
  ```bash
  black .
  flake8 .
  mypy apps/
  ```

---

## 📊 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (p95) | < 200ms | 145ms |
| Database Query Time | < 50ms | 32ms |
| Concurrent Users | 1000+ | 1500 |
| Test Coverage | > 80% | 87% |
| Uptime | 99.9% | 99.95% |

---

## 📞 Support

<table>
<tr>
<td>

### 📧 Contact
- **Email**: support@crowdfunding.io
- **Discord**: [Join Server](https://discord.gg/crowdfunding)
- **Twitter**: [@crowdfunding_io](https://twitter.com/crowdfunding_io)

</td>
<td>

### 📚 Resources
- [Full Documentation](https://docs.crowdfunding.io)
- [API Reference](https://api.crowdfunding.io/swagger/)
- [Video Tutorials](https://youtube.com/crowdfunding)

</td>
</tr>
</table>
>>>>>>> main

---

## 📄 License

<<<<<<< HEAD
This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Django & Django REST Framework**
=======
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### 🌟 Star this repo if you find it helpful!

**Built with ❤️ by the Crowdfunding Platform Team**

[⬆ Back to Top](#-crowdfunding-trading-platform)

</div>
>>>>>>> main
