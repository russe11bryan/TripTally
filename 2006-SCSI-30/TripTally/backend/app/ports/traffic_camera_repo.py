"""
Repository Port (Interface) for Traffic Camera Data
Part of the Model layer - defines contracts for persistence
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.models.traffic_camera import (
    CanonicalRow,
    ForecastVector,
    Camera
)


class ITrafficCameraRepo(ABC):
    """Port/Interface for traffic camera persistence"""
    
    @abstractmethod
    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Retrieve camera metadata"""
        pass
    
    @abstractmethod
    async def get_all_cameras(self) -> List[Camera]:
        """Retrieve all camera metadata"""
        pass
    
    @abstractmethod
    async def get_now(self, camera_id: str) -> Optional[CanonicalRow]:
        """Get current CI state for camera"""
        pass
    
    @abstractmethod
    async def save_now(self, row: CanonicalRow, ttl_sec: int = 600) -> None:
        """Save current CI state"""
        pass
    
    @abstractmethod
    async def get_forecast(self, camera_id: str) -> Optional[ForecastVector]:
        """Get forecast vector for camera"""
        pass
    
    @abstractmethod
    async def save_forecast(self, forecast: ForecastVector, ttl_sec: int = 600) -> None:
        """Save forecast vector"""
        pass
    
    @abstractmethod
    async def get_all_now(self) -> List[CanonicalRow]:
        """Get current state for all cameras"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if repository is healthy"""
        pass
