Issue Tracker – FastAPI + SvelteKit + PostgreSQL
A full-stack bug tracking system with role-based authentication:

Reporter: Can submit issues

Maintainer: Can triage issues

Admin: Can triage + perform CRUD on users/issues

Built with:

🚀 FastAPI (Python backend)

🎨 SvelteKit (JavaScript frontend)

🐘 PostgreSQL (relational DB)

🐳 Docker Compose (containerized dev env)

⚙️ Getting Started
✅ Prerequisites
Docker & Docker Compose

Google OAuth credentials (client ID + secret)

📦 Environment Variables
Create a .env in root:

env
Copy
Edit
# Database
POSTGRES_DB=auth_db
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=securepassword

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
FRONTEND_URL=http://localhost:5173
🚀 Run the App
bash
Copy
Edit
docker-compose up --build
Wait for:

nginx
Copy
Edit
Uvicorn running on http://0.0.0.0:8000
VITE dev server running on http://localhost:5173

🧪 Testing Flow
Visit http://localhost:5173/signup or /login

Create or login to a user

Google OAuth: click "Login with Google"

View authenticated user at /profile

🔐 Role Access
Role	Report Bug	Triage Bug	CRUD Users
Reporter	✅	❌	❌
Maintainer	✅	✅	❌
Admin	✅	✅	✅

🛠️ Backend Dependencies (requirements.txt)
css
Copy
Edit
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
📦 Docker Compose Overview
yaml
Copy
Edit
services:
  db:
    image: postgres:15
    ...
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=...
      - FRONTEND_URL=http://localhost:5173
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"