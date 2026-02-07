"""
Domain models for Parking facilities
"""
from dataclasses import dataclass
from typing import Optional
from .location import Location


@dataclass
class Carpark:
    id: int
    location_id: int
    hourly_rate: float = 0.0
    availability: int = 0


@dataclass
class BikeSharingPoint:
    id: int
    location_id: int
    bikes_available: int = 0
