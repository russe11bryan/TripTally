from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy_user_repo import SqlUserRepo
from app.adapters.sqlalchemy_saved_list_repo import SqlSavedListRepo
from app.api.deps import get_current_user, get_db_dep
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.account import User
from app.services.user_service import UserService
from app.services.google_oauth_service import GoogleOAuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    identifier: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    display_name: str
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None
    home_address: Optional[str] = None
    work_latitude: Optional[float] = None
    work_longitude: Optional[float] = None
    work_address: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_dep)):
    repo = SqlUserRepo(db)
    service = UserService(repo)
    identifier = payload.identifier.strip()
    if not identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifier is required")
    user = None
    if "@" in identifier:
        user = service.get_user_by_email(identifier.lower())
    if user is None:
        user = service.get_user_by_username(identifier.lower())
    
    # Check if user exists but has no password (Google-only account)
    if user and (user.hashed_password == "" or user.hashed_password is None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="This account uses Google Sign-In. Please sign in with Google or create an account under the same email."
        )
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=str(user.id), expires_delta=expires_delta)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        home_latitude=current_user.home_latitude,
        home_longitude=current_user.home_longitude,
        home_address=current_user.home_address,
        work_latitude=current_user.work_latitude,
        work_longitude=current_user.work_longitude,
        work_address=current_user.work_address,
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db_dep)):
    """
    Authenticate or create user via Google Sign-In.
    
    Client should send the Google ID token obtained from Google Sign-In.
    """
    repo = SqlUserRepo(db)
    list_repo = SqlSavedListRepo(db)
    google_service = GoogleOAuthService(
        repo, 
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_IOS_CLIENT_ID,
        saved_list_repo=list_repo
    )
    
    # Verify the Google token
    google_info = google_service.verify_google_token(payload.id_token)
    
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Extract user info from Google token
    google_id = google_info.get('sub')
    email = google_info.get('email', '')
    display_name = google_info.get('name', email.split('@')[0])
    
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required Google user information"
        )
    
    # Authenticate or create user
    user = google_service.authenticate_or_create_user(google_id, email, display_name)
    
    # Create access token
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=str(user.id), expires_delta=expires_delta)
    
    return TokenResponse(access_token=token)

