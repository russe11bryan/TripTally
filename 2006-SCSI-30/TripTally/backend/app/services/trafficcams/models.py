"""
Domain Models
Core business entities
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Camera:
    """Camera metadata"""
    camera_id: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None


@dataclass
class DetectionResult:
    """YOLO detection result"""
    boxes: list  # List of [x1, y1, x2, y2]
    scores: list
    class_ids: list
    vehicle_count: int
    weighted_count: float
    area_ratio: float
    inference_time_ms: float


@dataclass
class CIState:
    """Current Congestion Index state"""
    camera_id: str
    timestamp: datetime
    ci: float
    vehicle_count: int
    weighted_count: float
    area_ratio: float
    motion_score: float
    
    # Temporal features
    minute_of_day: int
    hour: int
    day_of_week: int
    is_weekend: bool
    sin_t_h: float
    cos_t_h: float
    
    # Image dimensions
    img_width: int
    img_height: int
    
    model_version: str = "simple_ci_v1"


@dataclass
class ForecastHorizon:
    """Single forecast point"""
    horizon_minutes: int
    predicted_ci: float
    confidence: float = 0.5
    forecast_time: Optional[datetime] = None


@dataclass
class CIForecast:
    """CI forecast for multiple horizons"""
    camera_id: str
    forecast_timestamp: datetime
    horizons: List[ForecastHorizon] = field(default_factory=list)
    model_version: str = "simple_ci_v1"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage"""
        data = {
            "ts": self.forecast_timestamp.isoformat(),
            "camera_id": self.camera_id,
            "model_ver": self.model_version
        }
        for h in self.horizons:
            data[f"h:{h.horizon_minutes}"] = str(h.predicted_ci)
        return data
