# Location Node
# domain/location.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Location:
    id: Optional[int]
    name: str
    lat: float
    lng: float
