# TaskForge — Multi-Tenant SaaS Task Management Platform

<p align="center">
  <strong>Production-grade task management platform with strict tenant isolation, RBAC, and enterprise-grade architecture.</strong>
</p>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React SPA (Vite + TypeScript)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │  Zustand  │ │ TanStack │ │  Router  │ │   Axios + Auth     │ │
│  │  Store    │ │  Query   │ │          │ │   Interceptors     │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────┴──────────────────────────────────┐
│                    FastAPI Application                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐ │
│  │  Routers   │ │ Middleware │ │  Services  │ │ Repositories │ │
│  │  (v1 API)  │ │ Rate Limit │ │  (Logic)   │ │  (Data)      │ │
│  │            │ │ Logging    │ │            │ │              │ │
│  │            │ │ Auth       │ │            │ │              │ │
│  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │ asyncpg
┌──────────────────────────────┴──────────────────────────────────┐
│               PostgreSQL 16 (Row-Level Security)                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  users │ organizations │ memberships │ tasks │ invites │ ...│ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Core
- **Multi-tenancy** — Shared DB, shared schema with PostgreSQL Row-Level Security
- **RBAC** — Owner / Admin / Member roles with middleware enforcement
- **JWT Auth** — Access (15min) + Refresh (7 day) tokens with bcrypt password hashing
- **Task Engine** — Full CRUD, status workflow (Todo → In Progress → In Review → Done), priority levels, assignment, due dates
- **Organization Mgmt** — Create orgs, invite users via tokens, switch between orgs

### Advanced SaaS
- **Activity Audit Trail** — Every mutation logged with user, action, entity, and JSONB changes
- **Pagination & Filtering** — Paginated task lists with status, priority, assignee, date, and search filters
- **Soft Deletes** — Tasks and memberships soft-deleted with `deleted_at` timestamp
- **Analytics** — Per-org stats (task counts by status, overdue, team size), per-user performance metrics
- **Structured Logging** — JSON logs with request_id, tenant_id, latency tracking
- **Rate Limiting** — Per-IP sliding window rate limiter

### Frontend
- **Dark SaaS UI** — Premium dark theme inspired by Linear, with glassmorphism and micro-animations
- **Dashboard** — Stats cards grid + activity feed
- **Task Views** — Data table with inline status changes + Kanban board
- **Org Switcher** — Dropdown to switch between organizations
- **Role-based UI** — Admin controls hidden from members

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (for PostgreSQL)
- **Python 3.12+**
- **Node.js 18+**

### 1. Clone & Setup

```bash
cd k:\Internship\taskforge
```

### 2. Start PostgreSQL

```bash
docker-compose up -d
```

Wait for PostgreSQL to be healthy:
```bash
docker-compose ps
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy env file (already provided)
# Edit .env if needed

# Run the backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The frontend will be available at: `http://localhost:5173`

### 5. First User Flow

1. Open `http://localhost:5173`
2. Register a new account
3. Navigate to **Settings** → Create an organization
4. Start creating tasks!

---

## 📁 Project Structure

```
taskforge/
├── backend/
│   ├── app/
│   │   ├── main.py              # App factory + middleware
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # Async SQLAlchemy + tenant sessions
│   │   ├── dependencies.py      # DI: auth, RBAC, tenant context
│   │   ├── exceptions.py        # Custom HTTP exceptions
│   │   ├── middleware/           # Rate limiter, logging
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── repositories/        # Data access layer
│   │   ├── services/            # Business logic layer
│   │   ├── routers/v1/          # API route handlers
│   │   └── utils/               # JWT, pagination helpers
│   ├── scripts/init.sql         # PostgreSQL init (roles, extensions)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios client + endpoint modules
│   │   ├── components/          # Shared UI (Sidebar)
│   │   ├── features/            # Feature pages (auth, tasks, etc.)
│   │   ├── store/               # Zustand stores
│   │   ├── types/               # TypeScript definitions
│   │   ├── utils/               # Formatters, permissions
│   │   ├── App.tsx              # Router + layout
│   │   └── index.css            # Design system
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🔒 API Endpoints

### Auth — `/api/v1/auth/`
| Method | Path | Auth | Description |
|:--|:--|:--|:--|
| POST | `/register` | No | Register new user |
| POST | `/login` | No | Login → tokens |
| POST | `/refresh` | No | Refresh access token |
| GET | `/me` | Yes | Current user profile |

### Organizations — `/api/v1/organizations/`
| Method | Path | Auth | Description |
|:--|:--|:--|:--|
| POST | `/` | Yes | Create org (becomes owner) |
| GET | `/` | Yes | List user's orgs |
| GET | `/{id}` | Member | Get org details |
| PATCH | `/{id}` | Admin+ | Update org |
| GET | `/{id}/members` | Member | List members |
| DELETE | `/{id}/members/{uid}` | Admin+ | Remove member |
| PATCH | `/{id}/members/{uid}/role` | Owner | Change role |

### Tasks — `/api/v1/organizations/{org_id}/tasks/`
| Method | Path | Auth | Description |
|:--|:--|:--|:--|
| POST | `/` | Member | Create task |
| GET | `/` | Member | List (paginated, filtered) |
| GET | `/{id}` | Member | Get task detail |
| PATCH | `/{id}` | Member | Update task |
| PATCH | `/{id}/status` | Member | Change status (validated) |
| PATCH | `/{id}/assign` | Member | Assign/unassign |
| DELETE | `/{id}` | Admin+ | Soft delete |

### Invites — `/api/v1/.../invites/`
| Method | Path | Auth | Description |
|:--|:--|:--|:--|
| POST | `/organizations/{id}/invites/` | Admin+ | Send invite |
| GET | `/organizations/{id}/invites/` | Admin+ | List pending |
| DELETE | `/organizations/{id}/invites/{id}` | Admin+ | Revoke |
| POST | `/invites/accept` | Yes | Accept via token |

### Analytics — `/api/v1/organizations/{org_id}/analytics/`
| Method | Path | Auth | Description |
|:--|:--|:--|:--|
| GET | `/overview` | Member | Task stats |
| GET | `/user-performance` | Admin+ | Per-user metrics |
| GET | `/activity-feed` | Member | Audit trail |

---

## 🔐 Security

| Threat | Mitigation |
|:--|:--|
| SQL Injection | SQLAlchemy parameterized queries |
| XSS | React auto-escaping |
| Cross-tenant leaks | PostgreSQL RLS + service-layer tenant checks |
| Password exposure | bcrypt hashing (work factor 12) |
| Token theft | Short-lived access tokens (15min) |
| Brute force | Rate limiting (60 req/min per IP) |
| Input validation | Pydantic schemas on all endpoints |

---

## 🛠 Tech Stack

| Component | Technology |
|:--|:--|
| Backend | Python 3.12 + FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | JWT (python-jose) + bcrypt |
| State | Zustand + TanStack Query |
| Styling | Vanilla CSS design system |
| Containers | Docker Compose |

---

## 📋 Environment Variables

### Backend (`.env`)
```env
DATABASE_URL=postgresql+asyncpg://taskforge:taskforge_secret_2024@localhost:5432/taskforge
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:5173
RATE_LIMIT_PER_MINUTE=60
LOG_LEVEL=INFO
DEBUG=true
```

### Frontend (`.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 📄 License

MIT
