from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from legal_ai.core.database import get_db
from legal_ai.service.auth_service import get_user_by_username, create_user, verify_password, get_password_hash
from legal_ai.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from legal_ai.db.models import User
from pydantic import BaseModel, Field

router = APIRouter()

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create user using the service function which handles password hashing
    return create_user(db=db, user=user)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For a local app, we might just return the user info or a simple token
    # Here we return a dummy token for simplicity, in production use JWT
    return {"access_token": user.username, "token_type": "bearer", "user_id": user.id}
