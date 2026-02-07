"""
Domain model for SavedList (e.g., Favourites, Travel Plans, etc.)
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SavedList:
    id: Optional[int]
    user_id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
