from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from auth.password_handler import hash_password
from app.schemas import UserCreate

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

async def get_or_create_oauth_user(db, provider: str, sub: str, email: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(email=email, oauth_provider=provider, oauth_sub=sub)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

