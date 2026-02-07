from __future__ import annotations

# Pydantic request/response models for route
from pydantic import BaseModel, Field
from typing import Optional


class RouteCreate(BaseModel):
    """Schema for creating a new route."""
    start_location_id: int = Field(..., description="Starting location ID")
    end_location_id: int = Field(..., description="Ending location ID")
    subtype: str = Field(..., description="Route subtype: recommended, alternate, user_suggested")
    transport_mode: str = Field(default="", description="Mode of transport: driving, walking, cycling, public_transport")
    route_line: list[int] = Field(default_factory=list, description="List of LocationNode IDs forming the route")
    distance_km: Optional[float] = Field(default=None, description="Route distance in kilometers")
    duration_min: Optional[float] = Field(default=None, description="Route duration in minutes")
    metrics_id: Optional[int] = Field(default=None, description="Associated metrics ID")


class UserSuggestedRouteCreate(RouteCreate):
    """Schema for creating a user-suggested route."""
    user_id: int = Field(..., description="ID of the user suggesting the route")
    subtype: str = Field(default="user_suggested", description="Always 'user_suggested' for this type")


class RouteUpdate(BaseModel):
    """Schema for updating a route."""
    transport_mode: Optional[str] = None
    route_line: Optional[list[int]] = None
    distance_km: Optional[float] = None
    duration_min: Optional[float] = None
    metrics_id: Optional[int] = None


class RouteOut(BaseModel):
    """Schema for route response."""
    id: int
    start_location_id: int
    end_location_id: int
    subtype: str
    transport_mode: str
    route_line: list[int]
    metrics_id: Optional[int]
    type: str

    class Config:
        from_attributes = True


class UserSuggestedRouteOut(RouteOut):
    """Schema for user-suggested route response."""
    user_id: Optional[int] = None
    type: str = "user_suggested"

    class Config:
        from_attributes = True

