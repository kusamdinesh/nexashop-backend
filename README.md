# NexaShop Backend API 🛒

A production-grade e-commerce REST API built with **FastAPI** and **Python**, featuring dual database architecture, Redis caching, JWT authentication with RBAC, and automated email notifications.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────┐
│                  Angular Frontend                │
└──────────────────────┬──────────────────────────┘
│ HTTP/REST
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend (/api/v1)           │
│                                                  │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │    Auth     │  │ Products │  │  Customers │  │
│  │ JWT+Argon2  │  │  CRUD    │  │   CRUD     │  │
│  └─────────────┘  └──────────┘  └────────────┘  │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │   Orders    │  │Inventory │  │ Analytics  │  │
│  │   CRUD      │  │  Stock   │  │  Charts    │  │
│  └─────────────┘  └──────────┘  └────────────┘  │
└────────┬──────────────┬───────────────┬──────────┘
│              │               │
┌────────▼───┐  ┌───────▼────┐  ┌──────▼──────┐
│ PostgreSQL │  │  MongoDB   │  │    Redis    │
│ Relational │  │ Activity   │  │   Cache     │
│    Data    │  │   Logs     │  │   Layer     │
└────────────┘  └────────────┘  └─────────────┘

---

## ✨ Features

### Core
- **Versioned REST API** — `/api/v1` with auto-generated Swagger docs
- **Dual Database** — PostgreSQL for relational data + MongoDB for activity logs and analytics
- **Redis Caching** — Cache-aside pattern with automatic invalidation
- **JWT Authentication** — Secure token-based auth with 60-minute expiry
- **Argon2id Password Hashing** — OWASP #1 recommended algorithm
- **Role Based Access Control** — Admin, Manager, Staff roles enforced at API level
- **Soft Deletes** — Data is never permanently deleted
- **Pagination & Search** — All list endpoints support filtering and pagination

### Modules
- 🔐 **Auth** — Register, Login, JWT tokens, /me endpoint
- 📦 **Products** — CRUD, categories, SKU management, stock tracking
- 👥 **Customers** — CRUD, address management, purchase history tracking
- 🛒 **Orders** — Multi-item orders, status lifecycle, automatic stock deduction
- 🏭 **Inventory** — Stock adjustments, history logging to MongoDB
- 📊 **Analytics** — Revenue over time, orders by status, customer growth
- 👤 **Users** — User management, role assignment (Admin only)

### Infrastructure
- 🐳 **Docker** — Fully containerized with Docker Compose
- 📧 **Email** — SendGrid transactional emails (order confirmation, status updates, low stock alerts)
- 🔄 **CI/CD** — GitHub Actions with security scanning and Docker Hub deployment

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.100+ |
| Language | Python 3.11 |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Relational DB | PostgreSQL 16 |
| NoSQL DB | MongoDB 7 |
| Cache | Redis 7 |
| Auth | JWT (python-jose) |
| Password | Argon2id (passlib) |
| Email | SendGrid |
| Templates | Jinja2 |
| Container | Docker + Nginx |
| CI/CD | GitHub Actions |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16
- MongoDB 7
- Redis 7

### Local Setup

```bash
# Clone the repo
git clone https://github.com/kusamdinesh/nexashop-backend.git
cd nexashop-backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Start the server
uvicorn main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

### Docker Setup

```bash
# Clone both repos into the same parent folder
git clone https://github.com/kusamdinesh/nexashop-backend.git
git clone https://github.com/kusamdinesh/nexashop-frontend.git
git clone https://github.com/kusamdinesh/nexashop-docker.git

cd nexashop-docker
docker compose up --build
```

---

## 📁 Project Structure

nexashop-backend/
├── main.py                 # App entry point
├── database.py             # PostgreSQL + MongoDB connections
├── seed.py                 # Seed database with sample data
├── requirements.txt
├── Dockerfile
├── .env.example
├── config/
│   ├── settings.py         # Pydantic settings
│   ├── auth_utils.py       # JWT + Argon2id + RBAC dependencies
│   └── email_service.py    # SendGrid email service
├── models/                 # SQLAlchemy ORM models
│   ├── user.py
│   ├── product.py
│   ├── customer.py
│   ├── order.py
│   └── inventory.py
├── routes/                 # FastAPI route handlers
│   ├── auth.py
│   ├── products.py
│   ├── customers.py
│   ├── orders.py
│   ├── inventory.py
│   ├── analytics.py
│   └── users.py
├── schemas/                # Pydantic request/response schemas
│   ├── user.py
│   ├── product.py
│   ├── customer.py
│   └── order.py
├── templates/
│   └── emails/             # Jinja2 HTML email templates
│       ├── welcome.html
│       ├── order_confirmation.html
│       ├── order_status_update.html
│       └── low_stock_alert.html
└── tests/
└── test_main.py

---

## 🔐 API Authentication

All endpoints except `/api/v1/auth/register` and `/api/v1/auth/login` require a JWT token.

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@nexashop.com" \
  -F "password=Admin123!"

# Use token
curl http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 👥 Default Users (after seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@nexashop.com | Admin123! |
| Manager | manager@nexashop.com | Manager123! |
| Staff | staff@nexashop.com | Staff123! |

---

## 🔒 RBAC Permissions

| Endpoint | Admin | Manager | Staff |
|----------|-------|---------|-------|
| View products/customers/orders | ✅ | ✅ | ✅ |
| Create/Edit products/customers | ✅ | ✅ | ❌ |
| Delete products/customers | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| View analytics | ✅ | ✅ | ❌ |

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/products/` | List products with search/pagination |
| POST | `/api/v1/products/` | Create product |
| GET | `/api/v1/customers/` | List customers |
| POST | `/api/v1/orders/` | Create order |
| PATCH | `/api/v1/orders/{id}/status` | Update order status |
| GET | `/api/v1/inventory/` | Get inventory levels |
| POST | `/api/v1/inventory/adjust` | Adjust stock |
| GET | `/api/v1/analytics/summary` | Get analytics summary |
| GET | `/api/v1/users/` | List users (Admin only) |

Full API docs available at `/docs` when running locally.

---

## 🧪 Running Tests

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 🐳 CI/CD Pipeline

Every push to `main` triggers:

Code Quality → Security Scan → Tests → SonarCloud → Docker Build → Push to Docker Hub

Docker images available at:
- `kusamdinesh/nexashop-backend:latest`
- `kusamdinesh/nexashop-frontend:latest`

---

## 📧 Email Notifications

| Trigger | Recipient | Email Type |
|---------|-----------|------------|
| User registers | New user | Welcome email |
| Order placed | Customer | Order confirmation |
| Order status changes | Customer | Status update |
| Stock drops below 10 | Admin | Low stock alert |

---

## 🤝 Related Repositories

- [nexashop-frontend](https://github.com/kusamdinesh/nexashop-frontend) — Angular 19 frontend
- [nexashop-docker](https://github.com/kusamdinesh/nexashop-docker) — Docker Compose setup