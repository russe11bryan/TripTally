from __future__ import annotations

"""
Domain models for Routes
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Route:
    id: int
    start_location_id: int
    end_location_id: int
    subtype: str  # "recommended", "alternate", "user_suggested"
    transport_mode: str = ""
    route_line: list[int] = field(default_factory=list)  # List of LocationNode IDs
    metrics_id: Optional[int] = None  # Reference to associated Metrics
    type: str = "route"


@dataclass
class UserSuggestedRoute(Route):
    user_id: Optional[int] = None
    type: str = "user_suggested"
