from pydantic import BaseModel
from typing import Optional, List, Dict

class DirectionsRoute(BaseModel):
    route_id: int
    summary: Optional[str] = ""
    distance: int
    distance_text: str
    duration: int
    duration_text: str
    duration_in_traffic: Optional[int] = None
    duration_in_traffic_text: Optional[str] = None
    encoded_polyline: str
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    start_location: Optional[Dict[str, float]] = None  # {lat, lng}
    end_location: Optional[Dict[str, float]] = None    # {lat, lng}
    fare: Optional[str] = None  # transit only


class DirectionsResponse(BaseModel):
    status: str
    routes: List[DirectionsRoute]
    overview_polyline: Optional[str] = None
    destination: Optional[Dict[str, float]] = None
    distance_meters: Optional[int] = None
    duration_seconds: Optional[int] = None
    distance_text: Optional[str] = None
    duration_text: Optional[str] = None


 #New wrapper model for multiple sets
class MultiDirectionsResponse(BaseModel):
    results: List[DirectionsResponse]
