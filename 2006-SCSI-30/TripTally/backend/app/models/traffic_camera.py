"""
Traffic Camera Domain Models
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field


class Camera(BaseModel):
    """Camera metadata"""
    camera_id: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class CanonicalRow(BaseModel):
    """Canonical row representing current CI state"""
    ts: datetime
    camera_id: str
    
    # Image dimensions
    img_w: float
    img_h: float
    
    # Detection metrics
    veh_count: float
    veh_wcount: float
    area_ratio: float
    motion: float
    
    # Congestion Index
    CI: float
    
    # Temporal features
    minute_of_day: int
    hour: int
    day_of_week: int
    is_weekend: bool
    sin_t_h: float
    cos_t_h: float
    
    # Lag features (optional)
    CI_lag_1: Optional[float] = None
    CI_lag_3: Optional[float] = None
    CI_lag_6: Optional[float] = None
    CI_lag_12: Optional[float] = None
    CI_lag_30: Optional[float] = None
    CI_lag_60: Optional[float] = None
    
    # Rolling features (optional)
    CI_roll_mean_30: Optional[float] = None
    CI_roll_std_30: Optional[float] = None
    CI_roll_mean_60: Optional[float] = None
    
    model_ver: str = "simple_ci_v1"
    
    class Config:
        from_attributes = True


class ForecastHorizon(BaseModel):
    """Single forecast at a specific horizon"""
    horizon_min: int  # Minutes in future (2, 4, 6, ...)
    CI_pred: float    # Predicted CI value
    
    class Config:
        from_attributes = True


class ForecastVector(BaseModel):
    """Complete forecast vector for a camera"""
    camera_id: str
    forecast_ts: datetime  # When forecast was made
    horizons: List[ForecastHorizon]  # Predictions at different horizons
    model_ver: str = "simple_ci_v1"
    
    class Config:
        from_attributes = True


class NowDTO(BaseModel):
    """Data Transfer Object for current state API response"""
    ts: datetime
    camera_id: str
    CI: float
    veh_count: int
    area_ratio: float
    motion: float
    model_ver: str
    
    # Optional camera metadata
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Freshness indicator
    is_fresh: bool = Field(default=True, description="Data is < 5 minutes old")
    
    @classmethod
    def from_canonical(cls, row: CanonicalRow, camera: Optional[Camera] = None) -> "NowDTO":
        """Convert from canonical row"""
        age = (datetime.now(timezone.utc) - row.ts).total_seconds()
        is_fresh = age < 300  # 5 minutes
        
        return cls(
            ts=row.ts,
            camera_id=row.camera_id,
            CI=row.CI,
            veh_count=int(row.veh_count),
            area_ratio=row.area_ratio,
            motion=row.motion,
            model_ver=row.model_ver,
            latitude=camera.latitude if camera else None,
            longitude=camera.longitude if camera else None,
            is_fresh=is_fresh
        )
    
    class Config:
        from_attributes = True


class ForecastDTO(BaseModel):
    """Data Transfer Object for forecast API response"""
    ts: datetime
    forecast_ts: datetime
    camera_id: str
    horizons_min: List[int]
    CI_forecast: List[float]
    model_ver: str
    
    # Optional camera metadata
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Freshness indicator
    is_fresh: bool = Field(default=True, description="Forecast is < 10 minutes old")
    
    @classmethod
    def from_forecast_vector(cls, fcst: ForecastVector, camera: Optional[Camera] = None) -> "ForecastDTO":
        """Convert from forecast vector"""
        age = (datetime.now(timezone.utc) - fcst.forecast_ts).total_seconds()
        is_fresh = age < 600  # 10 minutes
        
        return cls(
            ts=datetime.now(timezone.utc),
            forecast_ts=fcst.forecast_ts,
            camera_id=fcst.camera_id,
            horizons_min=[h.horizon_min for h in fcst.horizons],
            CI_forecast=[h.CI_pred for h in fcst.horizons],
            model_ver=fcst.model_ver,
            latitude=camera.latitude if camera else None,
            longitude=camera.longitude if camera else None,
            is_fresh=is_fresh
        )
    
    class Config:
        from_attributes = True


class CameraListDTO(BaseModel):
    """Data Transfer Object for camera list API response"""
    cameras: List[NowDTO]
    total: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
