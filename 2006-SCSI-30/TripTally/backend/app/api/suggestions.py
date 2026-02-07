from __future__ import annotations

"""
Suggestion API endpoints for user recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.db import get_db
from app.adapters.sqlalchemy_suggestion_repo import SqlSuggestionRepo
from app.adapters.tables import UserLikeTable
from app.models.suggestion import Suggestion

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


# ============= Pydantic Schemas =============
class SuggestionCreate(BaseModel):
    title: str
    category: str
    description: str
    added_by: Optional[str] = None  # Username of submitter
    latitude: float  # Location latitude (required)
    longitude: float  # Location longitude (required)
    location_name: str  # Human-readable location name (required)


class SuggestionUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, approved, rejected
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None


class SuggestionResponse(BaseModel):
    id: int
    title: str
    category: str
    description: str
    added_by: Optional[str]
    created_at: Optional[datetime]
    status: str
    likes: int
    is_liked_by_user: bool = False  # Whether current user has liked this
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


class LikeRequest(BaseModel):
    user_id: int  # ID of the user liking the suggestion


# ============= API Endpoints =============
@router.post("", response_model=SuggestionResponse, status_code=201)
def create_suggestion(payload: SuggestionCreate, db: Session = Depends(get_db)):
    """Create a new suggestion/recommendation."""
    repo = SqlSuggestionRepo(db)
    suggestion = Suggestion(
        id=0,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        added_by=payload.added_by,
        created_at=datetime.now(),
        status="pending",
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name
    )
    created_suggestion = repo.add(suggestion)
    return created_suggestion


@router.get("", response_model=list[SuggestionResponse])
def list_suggestions(user_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all suggestions with like status for the current user.
    Optionally filter by status: pending, approved, rejected
    Pass user_id to get is_liked_by_user status
    """
    repo = SqlSuggestionRepo(db)
    if status:
        suggestions = repo.list_by_status(status)
    else:
        suggestions = repo.list()
    
    # If user_id provided, check which suggestions the user has liked
    if user_id:
        liked_suggestion_ids = {
            row[0] for row in db.execute(
                text("SELECT suggestion_id FROM user_likes WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchall()
        }
        
        # Add is_liked_by_user field to each suggestion
        result = []
        for suggestion in suggestions:
            suggestion_dict = {
                "id": suggestion.id,
                "title": suggestion.title,
                "category": suggestion.category,
                "description": suggestion.description,
                "added_by": suggestion.added_by,
                "created_at": suggestion.created_at,
                "status": suggestion.status,
                "likes": suggestion.likes,
                "is_liked_by_user": suggestion.id in liked_suggestion_ids,
                "latitude": suggestion.latitude,
                "longitude": suggestion.longitude,
                "location_name": suggestion.location_name
            }
            result.append(suggestion_dict)
        return result
    
    # If no user_id, return suggestions with is_liked_by_user = False
    return [
        {
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "description": s.description,
            "added_by": s.added_by,
            "created_at": s.created_at,
            "status": s.status,
            "likes": s.likes,
            "is_liked_by_user": False,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "location_name": s.location_name
        }
        for s in suggestions
    ]


@router.get("/{suggestion_id}", response_model=SuggestionResponse)
def get_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    """Get a suggestion by ID."""
    repo = SqlSuggestionRepo(db)
    suggestion = repo.get_by_id(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@router.patch("/{suggestion_id}", response_model=SuggestionResponse)
def update_suggestion(suggestion_id: int, payload: SuggestionUpdate, db: Session = Depends(get_db)):
    """Update a suggestion (e.g., change status to approved/rejected)."""
    repo = SqlSuggestionRepo(db)
    suggestion = repo.get_by_id(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Update fields if provided
    if payload.title is not None:
        suggestion.title = payload.title
    if payload.category is not None:
        suggestion.category = payload.category
    if payload.description is not None:
        suggestion.description = payload.description
    if payload.status is not None:
        if payload.status not in ["pending", "approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be pending, approved, or rejected")
        suggestion.status = payload.status
    
    updated_suggestion = repo.update(suggestion)
    return updated_suggestion


@router.delete("/{suggestion_id}", status_code=204)
def delete_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    """Delete a suggestion."""
    repo = SqlSuggestionRepo(db)
    success = repo.delete(suggestion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return None


@router.post("/{suggestion_id}/like", response_model=SuggestionResponse)
def like_suggestion(suggestion_id: int, payload: LikeRequest, db: Session = Depends(get_db)):
    """
    Like a suggestion (one like per user).
    Returns error if user already liked this suggestion.
    """
    repo = SqlSuggestionRepo(db)
    suggestion = repo.get_by_id(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Check if user already liked this suggestion
    existing_like = db.execute(
        text("SELECT id FROM user_likes WHERE user_id = :user_id AND suggestion_id = :suggestion_id"),
        {"user_id": payload.user_id, "suggestion_id": suggestion_id}
    ).fetchone()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this suggestion")
    
    # Add like record
    db.execute(
        text("INSERT INTO user_likes (user_id, suggestion_id, created_at) VALUES (:user_id, :suggestion_id, :created_at)"),
        {"user_id": payload.user_id, "suggestion_id": suggestion_id, "created_at": datetime.now().isoformat()}
    )
    db.commit()
    
    # Increment likes counter
    suggestion.likes += 1
    updated_suggestion = repo.update(suggestion)
    
    return {
        "id": updated_suggestion.id,
        "title": updated_suggestion.title,
        "category": updated_suggestion.category,
        "description": updated_suggestion.description,
        "added_by": updated_suggestion.added_by,
        "created_at": updated_suggestion.created_at,
        "status": updated_suggestion.status,
        "likes": updated_suggestion.likes,
        "is_liked_by_user": True
    }


@router.post("/{suggestion_id}/unlike", response_model=SuggestionResponse)
def unlike_suggestion(suggestion_id: int, payload: LikeRequest, db: Session = Depends(get_db)):
    """
    Unlike a suggestion (remove like).
    Returns error if user hasn't liked this suggestion.
    """
    repo = SqlSuggestionRepo(db)
    suggestion = repo.get_by_id(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Check if user has liked this suggestion
    existing_like = db.execute(
        text("SELECT id FROM user_likes WHERE user_id = :user_id AND suggestion_id = :suggestion_id"),
        {"user_id": payload.user_id, "suggestion_id": suggestion_id}
    ).fetchone()
    
    if not existing_like:
        raise HTTPException(status_code=400, detail="You haven't liked this suggestion")
    
    # Remove like record
    db.execute(
        text("DELETE FROM user_likes WHERE user_id = :user_id AND suggestion_id = :suggestion_id"),
        {"user_id": payload.user_id, "suggestion_id": suggestion_id}
    )
    db.commit()
    
    # Decrement likes counter (but don't go below 0)
    suggestion.likes = max(0, suggestion.likes - 1)
    updated_suggestion = repo.update(suggestion)
    
    return {
        "id": updated_suggestion.id,
        "title": updated_suggestion.title,
        "category": updated_suggestion.category,
        "description": updated_suggestion.description,
        "added_by": updated_suggestion.added_by,
        "created_at": updated_suggestion.created_at,
        "status": updated_suggestion.status,
        "likes": updated_suggestion.likes,
        "is_liked_by_user": False
    }
