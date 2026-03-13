from sqlalchemy.orm import Session
from passlib.context import CryptContext
from legal_ai.db.models import User
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user):
    # Debugging: Print password info
    print(f"DEBUG: Creating user '{user.username}'")
    print(f"DEBUG: Password type: {type(user.password)}")
    print(f"DEBUG: Password length: {len(user.password)}")
    print(f"DEBUG: Password content (safe first 3 chars): {user.password[:3]}...")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
