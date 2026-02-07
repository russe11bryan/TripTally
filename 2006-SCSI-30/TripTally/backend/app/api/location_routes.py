from __future__ import annotations

"""
API routes for Location endpoints.
Follows the Service + Repository pattern.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.db import get_db
from app.adapters.sqlalchemy_location_repo import SqlLocationRepo
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])


# ============= Pydantic Schemas =============
class LocationCreate(BaseModel):
    name: str
    lat: float
    lng: float


class LocationUpdate(BaseModel):
    name: str
    lat: float
    lng: float


class LocationResponse(BaseModel):
    id: int
    name: str
    lat: float
    lng: float

    class Config:
        from_attributes = True


# ============= API Endpoints =============
@router.post("", response_model=LocationResponse, status_code=201)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    """Create a new location."""
    repo = SqlLocationRepo(db)
    service = LocationService(repo)
    location = service.create_location(payload.name, payload.lat, payload.lng)
    return location


@router.get("", response_model=list[LocationResponse])
def list_locations(db: Session = Depends(get_db)):
    """Get all locations."""
    repo = SqlLocationRepo(db)
    service = LocationService(repo)
    return service.get_all_locations()


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a location by ID."""
    repo = SqlLocationRepo(db)
    service = LocationService(repo)
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, payload: LocationUpdate, db: Session = Depends(get_db)):
    """Update a location."""
    repo = SqlLocationRepo(db)
    service = LocationService(repo)
    location = service.update_location(location_id, payload.name, payload.lat, payload.lng)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete a location."""
    repo = SqlLocationRepo(db)
    service = LocationService(repo)
    success = service.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return None
