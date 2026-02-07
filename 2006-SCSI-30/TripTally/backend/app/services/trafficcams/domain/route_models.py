"""
Route Optimization Domain Models
Business entities for route-based traffic analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Tuple
from enum import Enum


@dataclass
class Point:
    """Geographic point (lat, lon)"""
    latitude: float
    longitude: float


@dataclass
class LineString:
    """Route represented as a series of points"""
    points: List[Point]
    
    def to_coordinates(self) -> List[Tuple[float, float]]:
        """Convert to list of (lat, lon) tuples"""
        return [(p.latitude, p.longitude) for p in self.points]


@dataclass
class RouteCameraInfo:
    """Camera information relevant to a route"""
    camera_id: str
    latitude: float
    longitude: float
    distance_to_route: float  # meters
    position_on_route: float  # 0.0 to 1.0 (start to end)


@dataclass
class CameraTrafficInfo:
    """Traffic information for a camera at a specific time"""
    camera_id: str
    current_ci: float
    forecast_ci: float  # CI at departure time
    timestamp: datetime


@dataclass
class DepartureOption:
    """Optimal departure time option"""
    departure_time: datetime
    minutes_from_now: int
    average_ci: float  # Average CI across all cameras on route
    max_ci: float  # Worst CI along route
    estimated_travel_time_minutes: float
    new_eta: datetime
    confidence_score: float  # 0.0 to 1.0
    camera_forecasts: List[CameraTrafficInfo] = field(default_factory=list)


@dataclass
class RouteOptimizationResult:
    """Complete route optimization result"""
    original_eta: datetime
    original_departure: datetime
    route_cameras: List[RouteCameraInfo]
    best_departure: DepartureOption
    alternative_departures: List[DepartureOption] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class TrafficLevel(Enum):
    """Traffic congestion levels"""
    FREE_FLOW = "free_flow"  # CI < 0.3
    LIGHT = "light"          # 0.3 <= CI < 0.5
    MODERATE = "moderate"    # 0.5 <= CI < 0.7
    HEAVY = "heavy"          # 0.7 <= CI < 0.9
    SEVERE = "severe"        # CI >= 0.9
    
    @classmethod
    def from_ci(cls, ci: float) -> 'TrafficLevel':
        """Classify CI into traffic level"""
        if ci < 0.3:
            return cls.FREE_FLOW
        elif ci < 0.5:
            return cls.LIGHT
        elif ci < 0.7:
            return cls.MODERATE
        elif ci < 0.9:
            return cls.HEAVY
        else:
            return cls.SEVERE
