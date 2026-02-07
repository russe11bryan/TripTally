from pydantic import BaseModel
from typing import Optional, List

class NearbyPlace(BaseModel):
    name: Optional[str] = None
    place_id: Optional[str] = None
    lat: float
    lng: float
    address: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    types: Optional[List[str]] = None
    open_now: Optional[bool] = None
    icon: Optional[str] = None

class NearbyResponse(BaseModel):
    status: str
    routes: List[NearbyPlace]   # keeping "routes" to match your existing UI contract
