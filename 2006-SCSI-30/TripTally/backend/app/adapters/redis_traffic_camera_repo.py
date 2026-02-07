"""
Redis Adapter for Traffic Camera Repository
Part of the Adapter layer - concrete implementation of persistence
"""

import json
import logging
from typing import Optional, List
from datetime import datetime
from redis.asyncio import Redis
from app.ports.traffic_camera_repo import ITrafficCameraRepo
from app.models.traffic_camera import (
    CanonicalRow,
    ForecastVector,
    Camera,
    ForecastHorizon
)

logger = logging.getLogger(__name__)


class RedisTrafficCameraRepo(ITrafficCameraRepo):
    """
    Redis implementation of traffic camera repository
    Uses Redis hashes for efficient storage and TTLs for auto-expiry
    
    Key patterns:
    - ci:now:<camera_id> - Current state (CanonicalRow)
    - ci:fcst:<camera_id> - Forecast vector (ForecastVector)
    - cameras:meta - Hash of all camera metadata
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self._cameras_cache: Optional[List[Camera]] = None
    
    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Retrieve camera metadata from Redis hash"""
        try:
            data = await self.redis.hget("cameras:meta", camera_id)
            if not data:
                return None
            cam_dict = json.loads(data)
            return Camera(**cam_dict)
        except Exception as e:
            logger.error(f"Error getting camera {camera_id}: {e}")
            return None
    
    async def get_all_cameras(self) -> List[Camera]:
        """Retrieve all camera metadata"""
        try:
            if self._cameras_cache:
                return self._cameras_cache
                
            data = await self.redis.hgetall("cameras:meta")
            cameras = [Camera(**json.loads(v)) for v in data.values()]
            self._cameras_cache = cameras
            return cameras
        except Exception as e:
            logger.error(f"Error getting all cameras: {e}")
            return []
    
    async def save_camera_metadata(self, cameras: List[Camera]) -> None:
        """Save camera metadata to Redis"""
        try:
            pipeline = self.redis.pipeline()
            for cam in cameras:
                pipeline.hset(
                    "cameras:meta",
                    cam.camera_id,
                    cam.model_dump_json()
                )
            await pipeline.execute()
            self._cameras_cache = cameras
            logger.info(f"Saved {len(cameras)} camera metadata entries")
        except Exception as e:
            logger.error(f"Error saving camera metadata: {e}")
    
    async def get_now(self, camera_id: str) -> Optional[CanonicalRow]:
        """Get current CI state for camera"""
        try:
            key = f"ci:now:{camera_id}"
            data = await self.redis.hgetall(key)
            
            if not data:
                return None
            
            # Convert Redis bytes to dict
            row_dict = {k.decode(): v.decode() for k, v in data.items()}
            
            # Parse datetime
            row_dict['ts'] = datetime.fromisoformat(row_dict['ts'])
            
            # Parse booleans
            row_dict['is_weekend'] = row_dict['is_weekend'].lower() == 'true'
            
            # Parse floats
            for key in ['img_w', 'img_h', 'veh_count', 'veh_wcount', 'area_ratio', 
                       'motion', 'CI', 'sin_t_h', 'cos_t_h']:
                if key in row_dict:
                    row_dict[key] = float(row_dict[key])
            
            # Parse optional floats
            for key in ['CI_lag_1', 'CI_lag_3', 'CI_lag_6', 'CI_lag_12', 
                       'CI_lag_30', 'CI_lag_60', 'CI_roll_mean_30', 
                       'CI_roll_std_30', 'CI_roll_mean_60']:
                if key in row_dict and row_dict[key] != 'None':
                    row_dict[key] = float(row_dict[key])
                else:
                    row_dict[key] = None
            
            # Parse ints
            for key in ['minute_of_day', 'hour', 'day_of_week']:
                if key in row_dict:
                    row_dict[key] = int(row_dict[key])
            
            return CanonicalRow(**row_dict)
            
        except Exception as e:
            logger.error(f"Error getting now for camera {camera_id}: {e}")
            return None
    
    async def save_now(self, row: CanonicalRow, ttl_sec: int = 600) -> None:
        """Save current CI state with TTL"""
        try:
            key = f"ci:now:{row.camera_id}"
            
            # Convert to dict for Redis hash
            row_dict = row.model_dump()
            row_dict['ts'] = row.ts.isoformat()
            
            # Convert None to string for Redis
            for k, v in row_dict.items():
                if v is None:
                    row_dict[k] = 'None'
            
            # Save to Redis with TTL
            pipeline = self.redis.pipeline()
            pipeline.hset(key, mapping=row_dict)
            pipeline.expire(key, ttl_sec)
            await pipeline.execute()
            
            logger.debug(f"Saved now for camera {row.camera_id}")
            
        except Exception as e:
            logger.error(f"Error saving now for camera {row.camera_id}: {e}")
    
    async def get_forecast(self, camera_id: str) -> Optional[ForecastVector]:
        """Get forecast vector for camera"""
        try:
            key = f"ci:fcst:{camera_id}"
            data = await self.redis.get(key)
            
            if not data:
                return None
            
            fcst_dict = json.loads(data)
            fcst_dict['forecast_ts'] = datetime.fromisoformat(fcst_dict['forecast_ts'])
            
            # Parse horizons
            fcst_dict['horizons'] = [
                ForecastHorizon(**h) for h in fcst_dict['horizons']
            ]
            
            return ForecastVector(**fcst_dict)
            
        except Exception as e:
            logger.error(f"Error getting forecast for camera {camera_id}: {e}")
            return None
    
    async def save_forecast(self, forecast: ForecastVector, ttl_sec: int = 600) -> None:
        """Save forecast vector with TTL"""
        try:
            key = f"ci:fcst:{forecast.camera_id}"
            
            # Convert to JSON
            fcst_dict = forecast.model_dump()
            fcst_dict['forecast_ts'] = forecast.forecast_ts.isoformat()
            
            # Save with TTL
            await self.redis.setex(
                key,
                ttl_sec,
                json.dumps(fcst_dict)
            )
            
            logger.debug(f"Saved forecast for camera {forecast.camera_id}")
            
        except Exception as e:
            logger.error(f"Error saving forecast for camera {forecast.camera_id}: {e}")
    
    async def get_all_now(self) -> List[CanonicalRow]:
        """Get current state for all cameras"""
        try:
            # Get all camera IDs
            cameras = await self.get_all_cameras()
            camera_ids = [cam.camera_id for cam in cameras]
            
            # Batch get all current states
            rows = []
            for camera_id in camera_ids:
                row = await self.get_now(camera_id)
                if row:
                    rows.append(row)
            
            return rows
            
        except Exception as e:
            logger.error(f"Error getting all now: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
