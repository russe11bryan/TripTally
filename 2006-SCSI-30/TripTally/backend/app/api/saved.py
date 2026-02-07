from __future__ import annotations

"""
API endpoints for saved lists and places.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.db import get_db
from app.adapters.sqlalchemy_saved_list_repo import SqlSavedListRepo
from app.adapters.sqlalchemy_saved_place_repo import SqlSavedPlaceRepo
from app.models.saved_list import SavedList
from app.models.saved_place import SavedPlace

router = APIRouter(prefix="/saved", tags=["saved"])


# ============= Schemas =============
class SavedListCreate(BaseModel):
    name: str
    user_id: int


class SavedListResponse(BaseModel):
    id: int
    user_id: int
    name: str
    place_count: int
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class SavedPlaceCreate(BaseModel):
    list_id: int
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float


class SavedPlaceResponse(BaseModel):
    id: int
    list_id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    created_at: Optional[str]

    class Config:
        from_attributes = True


# ============= Saved List Endpoints =============
@router.post("/lists", response_model=SavedListResponse, status_code=201)
def create_saved_list(
    list_data: SavedListCreate,
    db: Session = Depends(get_db)
):
    """Create a new saved list for a user."""
    repo = SqlSavedListRepo(db)
    
    saved_list = SavedList(
        id=None,
        user_id=list_data.user_id,
        name=list_data.name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    created_list = repo.add(saved_list)
    
    return SavedListResponse(
        id=created_list.id,
        user_id=created_list.user_id,
        name=created_list.name,
        place_count=0,
        created_at=created_list.created_at.isoformat() if created_list.created_at else None,
        updated_at=created_list.updated_at.isoformat() if created_list.updated_at else None,
    )


@router.get("/lists/user/{user_id}", response_model=list[SavedListResponse])
def list_user_saved_lists(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all saved lists for a specific user."""
    list_repo = SqlSavedListRepo(db)
    place_repo = SqlSavedPlaceRepo(db)
    
    lists = list_repo.list_by_user(user_id)
    
    return [
        SavedListResponse(
            id=lst.id,
            user_id=lst.user_id,
            name=lst.name,
            place_count=len(place_repo.list_by_list_id(lst.id)),
            created_at=lst.created_at.isoformat() if lst.created_at else None,
            updated_at=lst.updated_at.isoformat() if lst.updated_at else None,
        )
        for lst in lists
    ]


@router.get("/lists/{list_id}", response_model=SavedListResponse)
def get_saved_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific saved list by ID."""
    list_repo = SqlSavedListRepo(db)
    place_repo = SqlSavedPlaceRepo(db)
    
    saved_list = list_repo.get_by_id(list_id)
    
    if not saved_list:
        raise HTTPException(status_code=404, detail="Saved list not found")
    
    return SavedListResponse(
        id=saved_list.id,
        user_id=saved_list.user_id,
        name=saved_list.name,
        place_count=len(place_repo.list_by_list_id(saved_list.id)),
        created_at=saved_list.created_at.isoformat() if saved_list.created_at else None,
        updated_at=saved_list.updated_at.isoformat() if saved_list.updated_at else None,
    )


@router.delete("/lists/{list_id}", status_code=204)
def delete_saved_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """Delete a saved list."""
    repo = SqlSavedListRepo(db)
    success = repo.delete(list_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Saved list not found")
    
    return None


# ============= Saved Place Endpoints =============
@router.post("/places", response_model=SavedPlaceResponse, status_code=201)
def create_saved_place(
    place_data: SavedPlaceCreate,
    db: Session = Depends(get_db)
):
    """Add a new place to a saved list."""
    repo = SqlSavedPlaceRepo(db)
    
    saved_place = SavedPlace(
        id=None,
        list_id=place_data.list_id,
        name=place_data.name,
        address=place_data.address,
        latitude=place_data.latitude,
        longitude=place_data.longitude,
        created_at=datetime.utcnow(),
    )
    
    created_place = repo.add(saved_place)
    
    return SavedPlaceResponse(
        id=created_place.id,
        list_id=created_place.list_id,
        name=created_place.name,
        address=created_place.address,
        latitude=created_place.latitude,
        longitude=created_place.longitude,
        created_at=created_place.created_at.isoformat() if created_place.created_at else None,
    )


@router.get("/places/list/{list_id}", response_model=list[SavedPlaceResponse])
def list_places_in_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """Get all places in a saved list."""
    repo = SqlSavedPlaceRepo(db)
    places = repo.list_by_list_id(list_id)
    
    return [
        SavedPlaceResponse(
            id=place.id,
            list_id=place.list_id,
            name=place.name,
            address=place.address,
            latitude=place.latitude,
            longitude=place.longitude,
            created_at=place.created_at.isoformat() if place.created_at else None,
        )
        for place in places
    ]


@router.get("/places/{place_id}", response_model=SavedPlaceResponse)
def get_saved_place(
    place_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific saved place by ID."""
    repo = SqlSavedPlaceRepo(db)
    place = repo.get_by_id(place_id)
    
    if not place:
        raise HTTPException(status_code=404, detail="Saved place not found")
    
    return SavedPlaceResponse(
        id=place.id,
        list_id=place.list_id,
        name=place.name,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        created_at=place.created_at.isoformat() if place.created_at else None,
    )


@router.delete("/places/{place_id}", status_code=204)
def delete_saved_place(
    place_id: int,
    db: Session = Depends(get_db)
):
    """Delete a saved place."""
    repo = SqlSavedPlaceRepo(db)
    success = repo.delete(place_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Saved place not found")
    
    return None
