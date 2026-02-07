from __future__ import annotations

"""
API routes for User endpoints.
Follows the Service + Repository pattern.
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from app.core.db import get_db
from app.adapters.sqlalchemy_user_repo import SqlUserRepo
from app.adapters.sqlalchemy_saved_list_repo import SqlSavedListRepo
from app.services.user_service import UserService
from app.core.security import hash_password
from app.models.saved_list import SavedList

router = APIRouter(prefix="/users", tags=["Users"])


# ============= Helper Functions =============
def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    
    Requirements:
    - At least 8 characters
    - Contains at least one number
    - Contains at least one alphabet character
    - Contains at least one special character
    - No whitespace allowed
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for any whitespace characters (space, tab, newline, etc.)
    if re.search(r'\s', password):
        return False, "Password cannot contain whitespace"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def validate_email_format(email: str) -> tuple[bool, str]:
    """
    Validate email format beyond Pydantic's EmailStr.
    Returns (is_valid, error_message).
    """
    # Basic email pattern: xxx@domain
    email_pattern = r'^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format. Expected format: xxx@domain.com"
    return True, ""


def create_default_favourites_list(user_id: int, db: Session) -> SavedList:
    """Create a default 'Favourites' list for a new user."""
    list_repo = SqlSavedListRepo(db)
    favourites = SavedList(
        id=None,
        user_id=user_id,
        name="Favourites",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return list_repo.add(favourites)


# ============= Pydantic Schemas =============
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: str


class UserUpdate(BaseModel):
    email: EmailStr
    username: str
    display_name: str


class UserLocationUpdate(BaseModel):
    home_latitude: float | None = None
    home_longitude: float | None = None
    home_address: str | None = None
    work_latitude: float | None = None
    work_longitude: float | None = None
    work_address: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    display_name: str
    home_latitude: float | None = None
    home_longitude: float | None = None
    home_address: str | None = None
    work_latitude: float | None = None
    work_longitude: float | None = None
    work_address: str | None = None

    class Config:
        from_attributes = True


# ============= API Endpoints =============
@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    repo = SqlUserRepo(db)
    service = UserService(repo)
    email = payload.email.lower()
    username = payload.username.strip().lower()

    # Validate email format
    email_valid, email_error = validate_email_format(email)
    if not email_valid:
        raise HTTPException(status_code=400, detail=email_error)

    # Validate password strength
    password_valid, password_error = validate_password(payload.password)
    if not password_valid:
        raise HTTPException(status_code=400, detail=password_error)

    # Check if user already exists by email
    existing_user = service.get_user_by_email(email)
    if existing_user:
        # If user exists but has no password (Google sign-in only), allow them to add password
        if existing_user.hashed_password == "" or existing_user.hashed_password is None:
            # Check if the new username is taken by a DIFFERENT user
            existing_username = service.get_user_by_username(username)
            if existing_username and existing_username.id != existing_user.id:
                raise HTTPException(status_code=400, detail="Username already taken")
            
            # Update the existing user with password and username
            hashed_password = hash_password(payload.password)
            existing_user.hashed_password = hashed_password
            existing_user.username = username
            existing_user.display_name = payload.display_name
            updated_user = repo.update(existing_user)
            return updated_user
        else:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    existing_username = service.get_user_by_username(username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = hash_password(payload.password)

    user = service.create_user(email, username, hashed_password, payload.display_name)
    
    # Create default "Favourites" list for the new user
    create_default_favourites_list(user.id, db)
    
    return user


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Get all users."""
    repo = SqlUserRepo(db)
    service = UserService(repo)
    return service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID."""
    repo = SqlUserRepo(db)
    service = UserService(repo)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    repo = SqlUserRepo(db)
    service = UserService(repo)
    # Ensure username/email uniqueness if changed
    email = payload.email.lower()
    username = payload.username.strip().lower()

    existing_email = service.get_user_by_email(email)
    if existing_email and existing_email.id != user_id:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = service.get_user_by_username(username)
    if existing_username and existing_username.id != user_id:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = service.update_user(user_id, email, username, payload.display_name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    repo = SqlUserRepo(db)
    service = UserService(repo)
    success = service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None


@router.put("/{user_id}/locations", response_model=UserResponse)
def update_user_locations(
    user_id: int,
    payload: UserLocationUpdate,
    db: Session = Depends(get_db)
):
    """Update user's home and work locations."""
    repo = SqlUserRepo(db)
    user = repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update home location if provided
    if payload.home_latitude is not None:
        user.home_latitude = payload.home_latitude
    if payload.home_longitude is not None:
        user.home_longitude = payload.home_longitude
    if payload.home_address is not None:
        user.home_address = payload.home_address
    
    # Update work location if provided
    if payload.work_latitude is not None:
        user.work_latitude = payload.work_latitude
    if payload.work_longitude is not None:
        user.work_longitude = payload.work_longitude
    if payload.work_address is not None:
        user.work_address = payload.work_address
    # Get the fields that were explicitly provided in the request (including None values)
    update_data = payload.model_dump(exclude_unset=True)
    
    # Update home location fields (including null values to clear location)
    if 'home_latitude' in update_data:
        user.home_latitude = update_data['home_latitude']
    if 'home_longitude' in update_data:
        user.home_longitude = update_data['home_longitude']
    if 'home_address' in update_data:
        user.home_address = update_data['home_address']
    
    # Update work location fields (including null values to clear location)
    if 'work_latitude' in update_data:
        user.work_latitude = update_data['work_latitude']
    if 'work_longitude' in update_data:
        user.work_longitude = update_data['work_longitude']
    if 'work_address' in update_data:
        user.work_address = update_data['work_address']
    
    updated_user = repo.update(user)
    return updated_user
