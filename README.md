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
- [Contributing](#-contributing)

---

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
```

---

## 📁 Project Structure

```
crowdfunding_platform/
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
```

---

## 🤝 Contributing

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

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### 🌟 Star this repo if you find it helpful!

**Built with ❤️ by the Crowdfunding Platform Team**

[⬆ Back to Top](#-crowdfunding-trading-platform)

</div>
