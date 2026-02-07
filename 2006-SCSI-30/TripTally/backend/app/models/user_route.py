"""
Domain model for User-Created Routes
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class RoutePoint:
    """A point on the route with coordinates"""
    latitude: float
    longitude: float
    order: int  # Position in the route sequence


@dataclass
class UserRoute:
    """
    User-created or tracked routes that can be shared with the community.
    """
    id: int
    user_id: int
    title: str
    description: str = ""
    route_points: List[RoutePoint] = None  # List of lat/lng coordinates
    transport_mode: str = "walking"  # walking, driving, bicycling, transit
    distance: Optional[float] = None  # Distance in meters
    duration: Optional[int] = None  # Duration in seconds
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_public: bool = True  # Whether route is visible to other users
    likes: int = 0  # Number of likes
    created_by: Optional[str] = None  # Username of creator
    
    def __post_init__(self):
        if self.route_points is None:
            self.route_points = []


@dataclass
class UserRouteLike:
    """
    Tracks which users have liked which routes.
    """
    id: int
    user_id: int
    route_id: int
    created_at: Optional[datetime] = None
