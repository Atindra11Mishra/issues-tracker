import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import Response, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Optional, List
import enum
import aiofiles
import uuid

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://auth_user:securepassword@db:5432/auth_db")
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Google OAuth settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = "http://localhost:8000/oauth/google/callback"

# Simple role system - based on email addresses
ADMIN_EMAILS = ["admin@issues-tracker.com"]
MAINTAINER_EMAILS = ["maintainer@issues-tracker.com"]

def get_user_role(email: str) -> str:
    """Determine user role based on email"""
    if email in ADMIN_EMAILS:
        return "ADMIN"
    elif email in MAINTAINER_EMAILS:
        return "MAINTAINER"
    else:
        return "REPORTER"

# Database setup
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Issue status enum
class IssueStatus(str, enum.Enum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class IssueSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)
    oauth_sub = Column(String, nullable=True)
    
    # Relationship
    issues = relationship("Issue", back_populates="creator")

class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)  # Markdown content
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN, nullable=False)
    severity = Column(Enum(IssueSeverity), default=IssueSeverity.MEDIUM, nullable=False)
    file_path = Column(String, nullable=True)  # Path to uploaded file
    file_name = Column(String, nullable=True)  # Original filename
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship
    creator = relationship("User", back_populates="issues")

# Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class IssueCreate(BaseModel):
    title: str
    description: str
    severity: IssueSeverity = IssueSeverity.MEDIUM

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    severity: Optional[IssueSeverity] = None

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str
    status: IssueStatus
    severity: IssueSeverity
    file_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    creator_id: int
    
    class Config:
        from_attributes = True

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# JWT handling
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Auth dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

# CRUD operations
async def create_user(user_data: UserCreate, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if user:
        raise Exception("User already exists")
    
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"email": new_user.email, "id": new_user.id}

async def get_or_create_oauth_user(db: AsyncSession, provider: str, sub: str, email: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(email=email, oauth_provider=provider, oauth_sub=sub)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# FastAPI app
app = FastAPI(title="Issues Tracker API", version="1.0.0")

# Create uploads directory
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for file downloads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Debug: Print OAuth credentials
print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
print(f"GOOGLE_CLIENT_SECRET: {'***' if GOOGLE_CLIENT_SECRET else 'NOT SET'}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handle OPTIONS requests
@app.options("/{path:path}")
async def handle_options(path: str):
    return Response(status_code=200)

# Create tables and admin users on startup
@app.on_event("startup")
async def startup():
    print("Starting up application...")
    try:
        async with engine.begin() as conn:
            print("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully")
        
        # Create admin and maintainer users
        await create_admin_users()
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

async def create_admin_users():
    """Create admin and maintainer users if they don't exist"""
    async with AsyncSessionLocal() as db:
        try:
            # Create Admin user
            admin_email = "admin@issues-tracker.com"
            result = await db.execute(select(User).where(User.email == admin_email))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                admin_user = User(
                    email=admin_email,
                    hashed_password=hash_password("admin123")
                )
                db.add(admin_user)
                print(f"Created admin user: {admin_email}")
            
            # Create Maintainer user
            maintainer_email = "maintainer@issues-tracker.com"
            result = await db.execute(select(User).where(User.email == maintainer_email))
            maintainer_user = result.scalar_one_or_none()
            
            if not maintainer_user:
                maintainer_user = User(
                    email=maintainer_email,
                    hashed_password=hash_password("maintainer123")
                )
                db.add(maintainer_user)
                print(f"Created maintainer user: {maintainer_email}")
            
            await db.commit()
            print("Default users created successfully")
            print("🔑 Admin credentials: admin@issues-tracker.com / admin123")
            print("🔧 Maintainer credentials: maintainer@issues-tracker.com / maintainer123")
            
        except Exception as e:
            print(f"Error creating default users: {e}")
            await db.rollback()

# Routes
@app.get("/")
async def root():
    return {"message": "Issues Tracker API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/auth/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    print(f"Signup request received for email: {user.email}")
    try:
        result = await create_user(user, db)
        access_token = create_access_token(data={"sub": str(result["id"])})
        print(f"User created successfully: {result}")
        return {"access_token": access_token, "token_type": "bearer", "user": result}
    except Exception as e:
        print(f"Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.hashed_password:
        raise HTTPException(status_code=401, detail="Please login with your OAuth provider")
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    user_role = get_user_role(current_user.email)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": user_role,
        "oauth_provider": current_user.oauth_provider
    }

# Issues CRUD endpoints
@app.post("/issues", response_model=IssueResponse)
async def create_issue(
    title: str = Form(...),
    description: str = Form(...),
    severity: IssueSeverity = Form(IssueSeverity.MEDIUM),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new issue with optional file upload"""
    print(f"Creating issue: title={title}, user={current_user.email}")
    
    try:
        file_path = None
        file_name = None
        
        # Handle file upload
        if file and file.filename:
            print(f"Processing file upload: {file.filename}")
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            file_name = file.filename
            
            print(f"Saving file to: {file_path}")
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            print("File saved successfully")
        
        # Create issue
        print("Creating issue in database...")
        new_issue = Issue(
            title=title,
            description=description,
            severity=severity,
            file_path=file_path,
            file_name=file_name,
            creator_id=current_user.id
        )
        
        db.add(new_issue)
        await db.commit()
        await db.refresh(new_issue)
        print(f"Issue created successfully with ID: {new_issue.id}")
        
        return new_issue
        
    except Exception as e:
        print(f"Error creating issue: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")

@app.get("/issues", response_model=List[IssueResponse])
async def get_user_issues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get issues based on user role"""
    user_role = get_user_role(current_user.email)
    
    if user_role == "REPORTER":
        # Reporters can only see their own issues
        result = await db.execute(
            select(Issue).where(Issue.creator_id == current_user.id).order_by(Issue.created_at.desc())
        )
    else:
        # Maintainers and Admins can see all issues
        result = await db.execute(
            select(Issue).order_by(Issue.created_at.desc())
        )
    
    issues = result.scalars().all()
    return issues

@app.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific issue based on role permissions"""
    user_role = get_user_role(current_user.email)
    
    if user_role == "REPORTER":
        # Reporters can only see their own issues
        result = await db.execute(
            select(Issue).where(Issue.id == issue_id, Issue.creator_id == current_user.id)
        )
    else:
        # Maintainers and Admins can see all issues
        result = await db.execute(
            select(Issue).where(Issue.id == issue_id)
        )
    
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    return issue

@app.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    issue_update: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an issue based on role permissions"""
    user_role = get_user_role(current_user.email)
    
    # Get the issue first
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Check permissions
    if user_role == "REPORTER":
        # Reporters can only edit their own issues
        if issue.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only edit your own issues")
        
        # Reporters can only update title, description, and severity
        if issue_update.title is not None:
            issue.title = issue_update.title
        if issue_update.description is not None:
            issue.description = issue_update.description
        if issue_update.severity is not None:
            issue.severity = issue_update.severity
        # Status changes are NOT allowed for reporters
        if issue_update.status is not None:
            raise HTTPException(
                status_code=403, 
                detail="Reporters cannot change issue status. Only Maintainers and Admins can change status."
            )
    else:
        # Maintainers and Admins can update all fields of any issue
        if issue_update.title is not None:
            issue.title = issue_update.title
        if issue_update.description is not None:
            issue.description = issue_update.description
        if issue_update.status is not None:
            issue.status = issue_update.status
        if issue_update.severity is not None:
            issue.severity = issue_update.severity
    
    issue.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(issue)
        return issue
    except Exception as e:
        await db.rollback()
        print(f"Error updating issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to update issue")

@app.delete("/issues/{issue_id}")
async def delete_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an issue - Admins can delete any issue, others only their own"""
    user_role = get_user_role(current_user.email)
    
    if user_role == "ADMIN":
        # Admins can delete any issue
        result = await db.execute(select(Issue).where(Issue.id == issue_id))
    else:
        # Others can only delete their own issues
        result = await db.execute(
            select(Issue).where(Issue.id == issue_id, Issue.creator_id == current_user.id)
        )
    
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Delete associated file if exists
    if issue.file_path and os.path.exists(issue.file_path):
        os.remove(issue.file_path)
    
    await db.delete(issue)
    await db.commit()
    
    return {"message": "Issue deleted successfully"}

@app.get("/issues/{issue_id}/file")
async def download_issue_file(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download file associated with an issue"""
    user_role = get_user_role(current_user.email)
    
    if user_role == "REPORTER":
        # Reporters can only download files from their own issues
        result = await db.execute(
            select(Issue).where(Issue.id == issue_id, Issue.creator_id == current_user.id)
        )
    else:
        # Maintainers and Admins can download any file
        result = await db.execute(select(Issue).where(Issue.id == issue_id))
    
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if not issue.file_path or not os.path.exists(issue.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=issue.file_path,
        filename=issue.file_name,
        media_type='application/octet-stream'
    )

# Status workflow endpoints
@app.post("/issues/{issue_id}/advance")
async def advance_issue_status(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Advance issue to next status in workflow - Only Maintainers and Admins"""
    user_role = get_user_role(current_user.email)
    
    if user_role not in ["MAINTAINER", "ADMIN"]:
        raise HTTPException(
            status_code=403, 
            detail="Only Maintainers and Admins can advance issue status"
        )
    
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Status workflow: OPEN → TRIAGED → IN_PROGRESS → DONE
    status_workflow = {
        IssueStatus.OPEN: IssueStatus.TRIAGED,
        IssueStatus.TRIAGED: IssueStatus.IN_PROGRESS,
        IssueStatus.IN_PROGRESS: IssueStatus.DONE,
        IssueStatus.DONE: IssueStatus.DONE  # Already at final status
    }
    
    new_status = status_workflow.get(issue.status)
    if new_status == issue.status and issue.status == IssueStatus.DONE:
        raise HTTPException(status_code=400, detail="Issue is already at final status")
    
    issue.status = new_status
    issue.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(issue)
    
    return {"message": f"Issue status advanced to {new_status}", "issue": issue}

# Simple Google OAuth routes
@app.get("/oauth-test")
async def oauth_test():
    """Test OAuth routing"""
    return {"message": "OAuth routes are working", "google_configured": bool(GOOGLE_CLIENT_ID)}

@app.get("/google-auth")
async def google_auth_simple():
    """Initiate Google OAuth flow - alternative route"""
    print("Google OAuth endpoint called")
    
    if not GOOGLE_CLIENT_ID:
        return {"error": "Google OAuth not configured", "client_id": GOOGLE_CLIENT_ID}
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    google_auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    print(f"Redirecting to: {google_auth_url}")
    
    return RedirectResponse(url=google_auth_url)

@app.get("/oauth/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    print("Google OAuth endpoint called")
    
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    google_auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
    print(f"Redirecting to: {google_auth_url}")
    
    return RedirectResponse(url=google_auth_url)

@app.get("/oauth/google/callback")
async def google_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback"""
    if error:
        print(f"OAuth error: {error}")
        return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
    
    if not code:
        print("No authorization code received")
        return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
    
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_data = {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': GOOGLE_REDIRECT_URI
            }
            
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data
            )
            
            if token_response.status_code != 200:
                print(f"Token exchange failed: {token_response.text}")
                return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
            
            tokens = token_response.json()
            access_token = tokens.get('access_token')
            
            # Get user info from Google
            user_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if user_response.status_code != 200:
                print(f"Failed to get user info: {user_response.text}")
                return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
            
            user_info = user_response.json()
            print(f"Google user info: {user_info}")
            
            if not user_info.get('email'):
                print("No email in user info")
                return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
            
            # Create or get user
            user = await get_or_create_oauth_user(
                db=db,
                provider="google",
                sub=user_info['id'],
                email=user_info['email']
            )
            
            # Create JWT token
            jwt_token = create_access_token(data={"sub": str(user.id)})
            
            # Redirect to frontend with token
            return RedirectResponse(
                url=f"http://localhost:5173/auth/callback?token={jwt_token}"
            )
            
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)