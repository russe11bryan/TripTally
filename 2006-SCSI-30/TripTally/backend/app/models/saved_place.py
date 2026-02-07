"""
Domain model for SavedPlace (a place within a SavedList)
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SavedPlace:
    id: Optional[int]
    list_id: int
    name: str
    address: Optional[str] = None
    latitude: float = 0.0
    longitude: float = 0.0
    created_at: Optional[datetime] = None
