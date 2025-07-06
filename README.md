# 🐛 Issue Tracker – FastAPI + SvelteKit + PostgreSQL

A full-stack bug tracking system with secure login, Google OAuth, JWT auth, and role-based permissions.

### 🔐 Roles:

* **Reporter**: Can report issues
* **Maintainer**: Can triage issues
* **Admin**: Can triage + perform CRUD on all users/issues

---

## 📦 Tech Stack

* ⚙️ **FastAPI** – Python backend
* 🎨 **SvelteKit (JavaScript)** – frontend
* 🐘 **PostgreSQL** – database
* 🔐 **JWT + Google OAuth2** – authentication
* 🐳 **Docker Compose** – container orchestration

---

## 🚀 Getting Started

---

### 🔑 Environment Variables (`.env`)

```
# Database Configuration
POSTGRES_DB=auth_db
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=securepassword
DATABASE_URL=postgresql+asyncpg://auth_user:securepassword@db:5432/auth_db

# Google OAuth
GOOGLE_CLIENT_ID=xxxxxxxxx
GOOGLE_CLIENT_SECRET=xxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-make-it-very-long

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

---

### 🐳 Start Development

```bash
docker-compose up --build
```

> Backend: [http://localhost:8000](http://localhost:8000)
> Frontend: [http://localhost:5173](http://localhost:5173)

---

## 🔐 Auth Flow

* `POST /auth/signup` → email/password signup
* `POST /auth/login` → JWT login
* `GET /auth/me` → user info
* `GET /oauth/google` → login with Google

Google login will redirect with token to `FRONTEND_URL?token=...`

---

## 🧪 Testing Roles

| Role       | Report Bug | Triage | CRUD |
| ---------- | ---------- | ------ | ---- |
| Reporter   | ✅          | ❌      | ❌    |
| Maintainer | ✅          | ✅      | ❌    |
| Admin      | ✅          | ✅      | ✅    |

---

## 🧱 API Overview

| Method | Endpoint               | Description             |
| ------ | ---------------------- | ----------------------- |
| POST   | `/auth/signup`         | Register new user       |
| POST   | `/auth/login`          | Get JWT token           |
| GET    | `/auth/me`             | Fetch current user info |
| GET    | `/oauth/google`        | Login with Google       |
| POST   | `/issues/`             | Create issue            |
| GET    | `/issues/`             | List issues             |
| POST   | `/issues/{id}/advance` | Advance status          |
| DELETE | `/issues/{id}`         | Delete issue            |

---

## 📦 Backend Dependencies

```txt
fastapi
uvicorn[standard]
sqlalchemy
asyncpg
alembic
pydantic
email-validator
python-dotenv
passlib[bcrypt]
python-jose[cryptography]
authlib
httpx
psycopg2-binary
python-multipart
starlette
aiofiles
```

---

## 🗂️ Docker Compose Summary

```yaml
services:
  db:
    image: postgres:15
  backend:
    build: .
    ports:
      - "8000:8000"
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
```

---

## ✅ License

MIT — free to use, adapt, and deploy.
