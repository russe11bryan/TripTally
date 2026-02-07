"""
Domain model for User Suggestions/Recommendations
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Suggestion:
    """
    User-submitted recommendations for routes, activities, or places.
    """
    id: int
    title: str = ""
    category: str = ""
    description: str = ""
    added_by: Optional[str] = None  # Username of the person who submitted
    created_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, rejected
    likes: int = 0  # Number of likes/upvotes
    latitude: Optional[float] = None  # Location latitude
    longitude: Optional[float] = None  # Location longitude
    location_name: Optional[str] = None  # Human-readable location name
