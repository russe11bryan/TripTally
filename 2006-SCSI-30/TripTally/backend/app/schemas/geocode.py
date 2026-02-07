from pydantic import BaseModel
from typing import List, Optional

class GeocodeResult(BaseModel):
    formatted_address: str
    lat: float
    lng: float
    place_id: Optional[str] = None

class GeocodeResponse(BaseModel):
    status: str
    results: List[GeocodeResult]
