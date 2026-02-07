"""
Domain model for TrafficAlert
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TrafficAlert:
    id: int
    alert_id: str  # External alert ID or unique identifier
    obstruction_type: str  # Type of traffic alert/obstruction (e.g., Traffic, Accident, Road Closure, Police)
    latitude: float  # Location latitude
    longitude: float  # Location longitude
    location_name: Optional[str] = None  # Human-readable location name
    reported_by: Optional[int] = None  # User ID who reported
    delay_duration: Optional[float] = None  # Delay in minutes
    status: str = "active"  # active, resolved, expired
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
