from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from auth.dependencies import get_current_user
from app import crud, schemas
from app.models import User
from auth.password_handler import verify_password
from auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await crud.create_user(user, db)
        # Create access token for immediate login after signup
        access_token = create_access_token(data={"sub": str(result["id"])})
        return {"access_token": access_token, "token_type": "bearer", "user": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Query user by email (username field in OAuth2PasswordRequestForm)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user has a password (not OAuth user)
    if not user.hashed_password:
        raise HTTPException(status_code=401, detail="Please login with your OAuth provider")
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "oauth_provider": current_user.oauth_provider
    }