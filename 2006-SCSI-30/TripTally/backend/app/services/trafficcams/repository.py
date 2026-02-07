"""
Redis Repository Implementation
Implements DataRepository interface for Redis storage
"""

import redis
from typing import Optional, List
from datetime import datetime

from .data_repository import DataRepository
from .config import RedisConfig
from .models import CIState, CIForecast, Camera
from .logger import get_logger

logger = get_logger("redis_repo")


class RedisRepository(DataRepository):
    """Redis implementation of DataRepository"""
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.client = redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
    
    def ping(self) -> bool:
        """Test connection"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def save_ci_state(self, state: CIState) -> bool:
        """Save current CI state (implements DataRepository)"""
        key = f"ci:now:{state.camera_id}"
        data = {
            "ts": state.timestamp.isoformat(),
            "camera_id": state.camera_id,
            "CI": str(state.ci),
            "veh_count": str(state.vehicle_count),
            "veh_wcount": str(state.weighted_count),
            "area_ratio": str(state.area_ratio),
            "motion": str(state.motion_score),
            "img_w": str(state.img_width),
            "img_h": str(state.img_height),
            "minute_of_day": str(state.minute_of_day),
            "hour": str(state.hour),
            "day_of_week": str(state.day_of_week),
            "is_weekend": str(state.is_weekend),
            "sin_t_h": str(state.sin_t_h),
            "cos_t_h": str(state.cos_t_h),
            "model_ver": state.model_version
        }
        
        try:
            pipe = self.client.pipeline()
            pipe.hset(key, mapping=data)
            pipe.expire(key, self.config.ttl)
            pipe.execute()
            logger.debug(f"Saved CI state for camera {state.camera_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save CI state for {state.camera_id}: {e}")
            return False
    
    def save_forecast(self, forecast: CIForecast) -> bool:
        """Save forecast (implements DataRepository)"""
        key = f"ci:fcst:{forecast.camera_id}"
        data = forecast.to_dict()
        
        try:
            pipe = self.client.pipeline()
            pipe.hset(key, mapping=data)
            pipe.expire(key, self.config.ttl)
            pipe.execute()
            logger.debug(f"Saved forecast for camera {forecast.camera_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save forecast for {forecast.camera_id}: {e}")
            return False
    
    def save_camera_metadata(self, camera: Camera) -> bool:
        """Save camera metadata (implements DataRepository)"""
        try:
            data = {
                "camera_id": camera.camera_id,
                "latitude": str(camera.latitude),
                "longitude": str(camera.longitude)
            }
            self.client.hset("cameras:meta", camera.camera_id, str(data))
            logger.debug(f"Saved metadata for camera {camera.camera_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save metadata for {camera.camera_id}: {e}")
            return False
    
    def get_ci_state(self, camera_id: str) -> Optional[CIState]:
        """Get current CI state (implements DataRepository)"""
        key = f"ci:now:{camera_id}"
        try:
            data = self.client.hgetall(key)
            if not data:
                return None
            # Convert Redis hash to CIState object
            # For now return raw dict, could deserialize to CIState
            return data
        except Exception as e:
            logger.error(f"Failed to get CI state for {camera_id}: {e}")
            return None
    
    def get_forecast(self, camera_id: str) -> Optional[CIForecast]:
        """Get forecast (implements DataRepository)"""
        key = f"ci:fcst:{camera_id}"
        try:
            data = self.client.hgetall(key)
            if not data:
                return None
            # For now return raw dict, could deserialize to CIForecast
            return data
        except Exception as e:
            logger.error(f"Failed to get forecast for {camera_id}: {e}")
            return None
    
    def get_camera_metadata(self, camera_id: str) -> Optional[Camera]:
        """Get camera metadata (implements DataRepository)"""
        try:
            data = self.client.hget("cameras:meta", camera_id)
            if not data:
                return None
            # For now return raw data, could deserialize to Camera
            return data
        except Exception as e:
            logger.error(f"Failed to get metadata for {camera_id}: {e}")
            return None
    
    def list_cameras(self) -> List[str]:
        """List all camera IDs (implements DataRepository)"""
        try:
            return [k.decode() if isinstance(k, bytes) else k 
                   for k in self.client.hkeys("cameras:meta")]
        except Exception as e:
            logger.error(f"Failed to get camera IDs: {e}")
            return []
    
    def health_check(self) -> bool:
        """Health check (implements DataRepository)"""
        return self.ping()
    
    def get_repository_name(self) -> str:
        """Get repository name (implements DataRepository)"""
        return "Redis"
    
    def close(self) -> None:
        """Close connection"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
