# Routers (FastAPI endpoints)
import os
from functools import lru_cache
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from jose import JWTError

if TYPE_CHECKING:
    from redis.asyncio import Redis

from app.adapters.sqlalchemy_user_repo import SqlUserRepo
from app.services.user_service import UserService
from app.core.security import decode_access_token
from app.adapters.redis_traffic_camera_repo_v2 import RedisTrafficCameraRepoV2
from app.ports.traffic_camera_repo import ITrafficCameraRepo

def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> "User":
    from app.models.account import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = SqlUserRepo(db)
    service = UserService(repo)
    user = service.get_user(int(user_id))
    if not user:
        raise credentials_exception
    return user


# Traffic Camera Repository Dependencies

@lru_cache()
def get_redis_client():
    """
    Get Redis client singleton
    Reads configuration from environment variables
    """
    try:
        from redis.asyncio import Redis
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        return Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False  # We handle decoding manually
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis client not available. Please install redis package."
        )


def get_traffic_camera_repo() -> ITrafficCameraRepo:
    """
    Dependency injection for traffic camera repository
    Returns Redis implementation that integrates with forecasting service
    """
    redis_client = get_redis_client()
    return RedisTrafficCameraRepoV2(redis_client)
