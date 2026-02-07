"""
FastAPI routes for user-created routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.adapters.sqlalchemy_user_route_repo import SQLAlchemyUserRouteRepository
from app.adapters.tables import UserRouteLikeTable
from app.models.user_route import UserRoute, RoutePoint

router = APIRouter(prefix="/user-routes", tags=["user-routes"])


# ============= Pydantic Schemas =============
class RoutePointSchema(BaseModel):
    latitude: float
    longitude: float
    order: int


class UserRouteCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    route_points: List[RoutePointSchema]
    transport_mode: str = "walking"
    distance: Optional[float] = None
    duration: Optional[int] = None
    is_public: bool = True
    created_by: Optional[str] = None


class UserRouteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    route_points: Optional[List[RoutePointSchema]] = None
    transport_mode: Optional[str] = None
    distance: Optional[float] = None
    duration: Optional[int] = None
    is_public: Optional[bool] = None


class UserRouteResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    route_points: List[RoutePointSchema]
    transport_mode: str
    distance: Optional[float]
    duration: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    is_public: bool
    likes: int
    created_by: Optional[str]
    is_liked_by_user: bool = False
    
    class Config:
        from_attributes = True


# ============= API Endpoints =============

@router.post("", response_model=UserRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_user_route(
    route_data: UserRouteCreate,
    db: Session = Depends(get_db)
):
    """Create a new user route."""
    repo = SQLAlchemyUserRouteRepository(db)
    
    # Convert Pydantic models to domain models
    route_points = [
        RoutePoint(latitude=p.latitude, longitude=p.longitude, order=p.order)
        for p in route_data.route_points
    ]
    
    user_route = UserRoute(
        id=0,  # Will be set by database
        user_id=route_data.user_id,
        title=route_data.title,
        description=route_data.description,
        route_points=route_points,
        transport_mode=route_data.transport_mode,
        distance=route_data.distance,
        duration=route_data.duration,
        is_public=route_data.is_public,
        created_by=route_data.created_by
    )
    
    created_route = repo.create(user_route)
    
    return UserRouteResponse(
        id=created_route.id,
        user_id=created_route.user_id,
        title=created_route.title,
        description=created_route.description,
        route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in created_route.route_points],
        transport_mode=created_route.transport_mode,
        distance=created_route.distance,
        duration=created_route.duration,
        created_at=created_route.created_at.isoformat() if created_route.created_at else None,
        updated_at=created_route.updated_at.isoformat() if created_route.updated_at else None,
        is_public=created_route.is_public,
        likes=created_route.likes,
        created_by=created_route.created_by
    )


@router.get("", response_model=List[UserRouteResponse])
async def get_all_routes(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all public routes, optionally with like status for a user."""
    repo = SQLAlchemyUserRouteRepository(db)
    routes = repo.get_all_public(user_id=user_id)
    
    return [
        UserRouteResponse(
            id=r.id,
            user_id=r.user_id,
            title=r.title,
            description=r.description,
            route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in r.route_points],
            transport_mode=r.transport_mode,
            distance=r.distance,
            duration=r.duration,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
            is_public=r.is_public,
            likes=r.likes,
            created_by=r.created_by,
            is_liked_by_user=getattr(r, 'is_liked_by_user', False)
        )
        for r in routes
    ]


@router.get("/my-routes", response_model=List[UserRouteResponse])
async def get_my_routes(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all routes created by a specific user."""
    repo = SQLAlchemyUserRouteRepository(db)
    routes = repo.get_by_user(user_id)
    
    return [
        UserRouteResponse(
            id=r.id,
            user_id=r.user_id,
            title=r.title,
            description=r.description,
            route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in r.route_points],
            transport_mode=r.transport_mode,
            distance=r.distance,
            duration=r.duration,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
            is_public=r.is_public,
            likes=r.likes,
            created_by=r.created_by
        )
        for r in routes
    ]


@router.get("/{route_id}", response_model=UserRouteResponse)
async def get_route(
    route_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get a specific route by ID."""
    repo = SQLAlchemyUserRouteRepository(db)
    route = repo.get_by_id(route_id)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Check if user has liked this route
    is_liked = False
    if user_id:
        like_check = repo.db.query(repo.db.query(UserRouteLikeTable).filter(
            UserRouteLikeTable.route_id == route_id,
            UserRouteLikeTable.user_id == user_id
        ).exists()).scalar()
        is_liked = like_check
    
    return UserRouteResponse(
        id=route.id,
        user_id=route.user_id,
        title=route.title,
        description=route.description,
        route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in route.route_points],
        transport_mode=route.transport_mode,
        distance=route.distance,
        duration=route.duration,
        created_at=route.created_at.isoformat() if route.created_at else None,
        updated_at=route.updated_at.isoformat() if route.updated_at else None,
        is_public=route.is_public,
        likes=route.likes,
        created_by=route.created_by,
        is_liked_by_user=is_liked
    )


@router.put("/{route_id}", response_model=UserRouteResponse)
async def update_route(
    route_id: int,
    route_data: UserRouteUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing route."""
    repo = SQLAlchemyUserRouteRepository(db)
    existing_route = repo.get_by_id(route_id)
    
    if not existing_route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Update only provided fields
    if route_data.title is not None:
        existing_route.title = route_data.title
    if route_data.description is not None:
        existing_route.description = route_data.description
    if route_data.route_points is not None:
        existing_route.route_points = [
            RoutePoint(latitude=p.latitude, longitude=p.longitude, order=p.order)
            for p in route_data.route_points
        ]
    if route_data.transport_mode is not None:
        existing_route.transport_mode = route_data.transport_mode
    if route_data.distance is not None:
        existing_route.distance = route_data.distance
    if route_data.duration is not None:
        existing_route.duration = route_data.duration
    if route_data.is_public is not None:
        existing_route.is_public = route_data.is_public
    
    updated_route = repo.update(route_id, existing_route)
    
    return UserRouteResponse(
        id=updated_route.id,
        user_id=updated_route.user_id,
        title=updated_route.title,
        description=updated_route.description,
        route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in updated_route.route_points],
        transport_mode=updated_route.transport_mode,
        distance=updated_route.distance,
        duration=updated_route.duration,
        created_at=updated_route.created_at.isoformat() if updated_route.created_at else None,
        updated_at=updated_route.updated_at.isoformat() if updated_route.updated_at else None,
        is_public=updated_route.is_public,
        likes=updated_route.likes,
        created_by=updated_route.created_by
    )


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db)
):
    """Delete a route."""
    repo = SQLAlchemyUserRouteRepository(db)
    success = repo.delete(route_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return None


@router.post("/{route_id}/like", response_model=UserRouteResponse)
async def like_route(
    route_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Like a route."""
    repo = SQLAlchemyUserRouteRepository(db)
    
    # Check if route exists
    route = repo.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Add like
    success = repo.add_like(route_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Already liked this route")
    
    # Return updated route
    updated_route = repo.get_by_id(route_id)
    updated_route.is_liked_by_user = True
    
    return UserRouteResponse(
        id=updated_route.id,
        user_id=updated_route.user_id,
        title=updated_route.title,
        description=updated_route.description,
        route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in updated_route.route_points],
        transport_mode=updated_route.transport_mode,
        distance=updated_route.distance,
        duration=updated_route.duration,
        created_at=updated_route.created_at.isoformat() if updated_route.created_at else None,
        updated_at=updated_route.updated_at.isoformat() if updated_route.updated_at else None,
        is_public=updated_route.is_public,
        likes=updated_route.likes,
        created_by=updated_route.created_by,
        is_liked_by_user=True
    )


@router.post("/{route_id}/unlike", response_model=UserRouteResponse)
async def unlike_route(
    route_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Unlike a route."""
    repo = SQLAlchemyUserRouteRepository(db)
    
    # Check if route exists
    route = repo.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Remove like
    success = repo.remove_like(route_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Haven't liked this route")
    
    # Return updated route
    updated_route = repo.get_by_id(route_id)
    updated_route.is_liked_by_user = False
    
    return UserRouteResponse(
        id=updated_route.id,
        user_id=updated_route.user_id,
        title=updated_route.title,
        description=updated_route.description,
        route_points=[RoutePointSchema(latitude=p.latitude, longitude=p.longitude, order=p.order) for p in updated_route.route_points],
        transport_mode=updated_route.transport_mode,
        distance=updated_route.distance,
        duration=updated_route.duration,
        created_at=updated_route.created_at.isoformat() if updated_route.created_at else None,
        updated_at=updated_route.updated_at.isoformat() if updated_route.updated_at else None,
        is_public=updated_route.is_public,
        likes=updated_route.likes,
        created_by=updated_route.created_by,
        is_liked_by_user=False
    )
