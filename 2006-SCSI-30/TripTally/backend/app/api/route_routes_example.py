from __future__ import annotations

"""
Example: Route API implementation template.
Copy this pattern to create APIs for Reports, Parking, Metrics, etc.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.db import get_db
from app.adapters.sqlalchemy_route_repo import SqlRouteRepo
from app.models.route import Route, RecommendedRoute, AlternateRoute, UserSuggestedRoute

router = APIRouter(prefix="/routes", tags=["Routes"])


# ============= Pydantic Schemas =============
class RouteCreate(BaseModel):
    start_location_id: int
    end_location_id: int
    transport_mode: str
    route_type: str = "route"  # "recommended", "alternate", "user_suggested"
    user_id: Optional[int] = None


class RouteResponse(BaseModel):
    id: int
    start_location_id: Optional[int]
    end_location_id: Optional[int]
    transport_mode: str
    route_line: dict
    type: str

    class Config:
        from_attributes = True


# ============= Helper Function =============
def create_route_from_type(data: RouteCreate) -> Route:
    """Factory function to create the correct route type."""
    route_data = {
        "start_location_id": data.start_location_id,
        "end_location_id": data.end_location_id,
        "transport_mode": data.transport_mode,
    }
    
    if data.route_type == "recommended":
        return RecommendedRoute(**route_data)
    elif data.route_type == "alternate":
        return AlternateRoute(**route_data)
    elif data.route_type == "user_suggested":
        return UserSuggestedRoute(**route_data, user_id=data.user_id)
    else:
        return Route(**route_data)


# ============= API Endpoints =============
@router.post("", response_model=RouteResponse, status_code=201)
def create_route(payload: RouteCreate, db: Session = Depends(get_db)):
    """Create a new route."""
    repo = SqlRouteRepo(db)
    route = create_route_from_type(payload)
    created_route = repo.add(route)
    return created_route


@router.get("", response_model=list[RouteResponse])
def list_routes(db: Session = Depends(get_db)):
    """Get all routes."""
    repo = SqlRouteRepo(db)
    return repo.list()


@router.get("/user/{user_id}", response_model=list[RouteResponse])
def list_user_routes(user_id: int, db: Session = Depends(get_db)):
    """Get all routes suggested by a specific user."""
    repo = SqlRouteRepo(db)
    return repo.list_by_user(user_id)


@router.get("/{route_id}", response_model=RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a route by ID."""
    repo = SqlRouteRepo(db)
    route = repo.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """Delete a route."""
    repo = SqlRouteRepo(db)
    success = repo.delete(route_id)
    if not success:
        raise HTTPException(status_code=404, detail="Route not found")
    return None


# ============= Additional Usage Example =============
"""
To use this router, add to main.py:

from app.api.route_routes_example import router as route_router
app.include_router(route_router)

Then test with:

# Create a recommended route
curl -X POST "http://localhost:8000/routes" \
  -H "Content-Type: application/json" \
  -d '{
    "start_location_id": 1,
    "end_location_id": 2,
    "transport_mode": "bus",
    "route_type": "recommended"
  }'

# Get all routes
curl "http://localhost:8000/routes"

# Get user's suggested routes
curl "http://localhost:8000/routes/user/1"
"""
