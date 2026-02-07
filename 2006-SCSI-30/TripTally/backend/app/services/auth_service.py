# use-case business logic
from sqlalchemy.orm import Session
from app.models.account import User
from app.schemas.user import UserCreate
from passlib.hash import bcrypt

def create_user(db: Session, data: UserCreate) -> User:
    hashed = bcrypt.hash(data.password)
    user = User(email=data.email, username=data.email, hashed_password=hashed, display_name=data.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
