"""
Redis Traffic Camera Repository with Forecasting Service Integration
Adapter that bridges the forecasting service Redis format with the backend API
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


class RedisTrafficCameraRepoV2(ITrafficCameraRepo):
    """
    Redis implementation that integrates with the traffic camera forecasting service
    
    Key patterns from forecasting service:
    - ci:now:<camera_id> - Current state (Redis HASH)
    - ci:fcst:<camera_id> - Forecast (Redis HASH with h:2, h:4, etc.)
    - cameras:meta - Camera metadata (Redis HASH, per-camera JSON)
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self._cameras_cache: Optional[List[Camera]] = None
    
    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Retrieve camera metadata from Redis hash"""
        try:
            # Forecasting service stores as: HGET cameras:meta <camera_id>
            data = await self.redis.hget("cameras:meta", camera_id)
            if not data:
                return None
            
            # Data might be stored as string representation of dict (Python's str(dict))
            # or as JSON. Try both.
            data_str = data.decode() if isinstance(data, bytes) else data
            
            try:
                # Try JSON first
                cam_dict = json.loads(data_str)
            except json.JSONDecodeError:
                # Fall back to eval (safe because we control the source)
                import ast
                cam_dict = ast.literal_eval(data_str)
            
            # Map forecasting service fields to our model
            return Camera(
                camera_id=cam_dict.get('camera_id', camera_id),
                latitude=float(cam_dict.get('latitude', 0)),
                longitude=float(cam_dict.get('longitude', 0)),
                image_url=None  # Not stored by forecasting service
            )
        except Exception as e:
            logger.error(f"Error getting camera {camera_id}: {e}")
            return None
    
    async def get_all_cameras(self) -> List[Camera]:
        """Retrieve all camera metadata"""
        try:
            if self._cameras_cache:
                return self._cameras_cache
                
            data = await self.redis.hgetall("cameras:meta")
            cameras = []
            for k, v in data.items():
                try:
                    cam_id = k.decode() if isinstance(k, bytes) else k
                    cam_str = v.decode() if isinstance(v, bytes) else v
                    
                    # Try JSON first, fall back to Python literal eval
                    try:
                        cam_dict = json.loads(cam_str)
                    except json.JSONDecodeError:
                        import ast
                        cam_dict = ast.literal_eval(cam_str)
                    
                    cameras.append(Camera(
                        camera_id=cam_dict.get('camera_id', cam_id),
                        latitude=float(cam_dict.get('latitude', 0)),
                        longitude=float(cam_dict.get('longitude', 0))
                    ))
                except Exception as e:
                    logger.warning(f"Error parsing camera {cam_id}: {e}")
                    continue
            
            self._cameras_cache = cameras
            return cameras
        except Exception as e:
            logger.error(f"Error getting all cameras: {e}")
            return []
    
    async def get_now(self, camera_id: str) -> Optional[CanonicalRow]:
        """
        Get current CI state for camera from forecasting service format
        
        Forecasting service stores as Redis HASH:
        ci:now:<camera_id> with fields: ts, CI, veh_count, etc.
        """
        try:
            key = f"ci:now:{camera_id}"
            data = await self.redis.hgetall(key)
            
            if not data:
                logger.warning(f"No current data for camera {camera_id}")
                return None
            
            # Convert Redis bytes to dict
            row_dict = {}
            for k, v in data.items():
                key_str = k.decode() if isinstance(k, bytes) else k
                val_str = v.decode() if isinstance(v, bytes) else v
                row_dict[key_str] = val_str
            
            # Parse datetime
            row_dict['ts'] = datetime.fromisoformat(row_dict['ts'].replace('Z', '+00:00'))
            
            # Parse booleans
            row_dict['is_weekend'] = row_dict.get('is_weekend', 'false').lower() in ('true', '1')
            
            # Parse required floats
            for key in ['img_w', 'img_h', 'veh_count', 'veh_wcount', 'area_ratio', 
                       'motion', 'CI', 'sin_t_h', 'cos_t_h']:
                if key in row_dict:
                    row_dict[key] = float(row_dict[key])
                else:
                    # Set defaults if missing
                    row_dict[key] = 0.0
            
            # Parse required ints
            for key in ['minute_of_day', 'hour', 'day_of_week']:
                if key in row_dict:
                    row_dict[key] = int(float(row_dict[key]))
                else:
                    row_dict[key] = 0
            
            # Parse optional floats (lag and rolling features)
            for key in ['CI_lag_1', 'CI_lag_3', 'CI_lag_6', 'CI_lag_12', 
                       'CI_lag_30', 'CI_lag_60', 'CI_roll_mean_30', 
                       'CI_roll_std_30', 'CI_roll_mean_60']:
                if key in row_dict and row_dict[key] not in ('None', '', 'null'):
                    try:
                        row_dict[key] = float(row_dict[key])
                    except:
                        row_dict[key] = None
                else:
                    row_dict[key] = None
            
            # Get model version
            row_dict['model_ver'] = row_dict.get('model_ver', 'simple_ci_v1')
            
            return CanonicalRow(**row_dict)
            
        except Exception as e:
            logger.error(f"Error getting now for camera {camera_id}: {e}", exc_info=True)
            return None
    
    async def save_now(self, row: CanonicalRow, ttl_sec: int = 600) -> None:
        """Save current CI state (for compatibility, not used by forecasting service)"""
        try:
            key = f"ci:now:{row.camera_id}"
            
            # Convert to dict for Redis hash
            row_dict = row.model_dump()
            row_dict['ts'] = row.ts.isoformat()
            
            # Convert None to string for Redis
            for k, v in row_dict.items():
                if v is None:
                    row_dict[k] = 'None'
                else:
                    row_dict[k] = str(v)
            
            # Save to Redis with TTL
            pipeline = self.redis.pipeline()
            pipeline.hset(key, mapping=row_dict)
            pipeline.expire(key, ttl_sec)
            await pipeline.execute()
            
            logger.debug(f"Saved now for camera {row.camera_id}")
            
        except Exception as e:
            logger.error(f"Error saving now for camera {row.camera_id}: {e}")
    
    async def get_forecast(self, camera_id: str) -> Optional[ForecastVector]:
        """
        Get forecast vector for camera from forecasting service format
        
        Forecasting service stores as Redis HASH:
        ci:fcst:<camera_id> with fields:
        - ts: forecast timestamp
        - camera_id: camera ID
        - model_ver: model version
        - h:2, h:4, h:6, ..., h:120: predicted CI values (60 total)
        """
        try:
            key = f"ci:fcst:{camera_id}"
            data = await self.redis.hgetall(key)
            
            if not data:
                logger.warning(f"No forecast for camera {camera_id}")
                return None
            
            # Convert Redis bytes to dict
            forecast_dict = {}
            for k, v in data.items():
                key_str = k.decode() if isinstance(k, bytes) else k
                val_str = v.decode() if isinstance(v, bytes) else v
                forecast_dict[key_str] = val_str
            
            # Extract metadata
            forecast_ts_str = forecast_dict.get('ts')
            if not forecast_ts_str:
                logger.error(f"No timestamp in forecast for {camera_id}")
                return None
            
            forecast_ts = datetime.fromisoformat(forecast_ts_str.replace('Z', '+00:00'))
            model_ver = forecast_dict.get('model_ver', 'simple_ci_v1')
            
            # Extract all horizon predictions (h:2, h:4, ..., h:120)
            horizons = []
            for key_str, val_str in forecast_dict.items():
                if key_str.startswith('h:'):
                    try:
                        horizon_min = int(key_str.split(':')[1])
                        ci_pred = float(val_str)
                        horizons.append(ForecastHorizon(
                            horizon_min=horizon_min,
                            CI_pred=ci_pred
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing horizon {key_str}: {e}")
                        continue
            
            if not horizons:
                logger.error(f"No horizon predictions found for camera {camera_id}")
                return None
            
            # Sort by horizon
            horizons.sort(key=lambda h: h.horizon_min)
            
            return ForecastVector(
                camera_id=camera_id,
                forecast_ts=forecast_ts,
                horizons=horizons,
                model_ver=model_ver
            )
            
        except Exception as e:
            logger.error(f"Error getting forecast for camera {camera_id}: {e}", exc_info=True)
            return None
    
    async def save_forecast(self, forecast: ForecastVector, ttl_sec: int = 600) -> None:
        """Save forecast vector (for compatibility, not typically used)"""
        try:
            key = f"ci:fcst:{forecast.camera_id}"
            
            # Build forecast dict in forecasting service format
            forecast_dict = {
                'ts': forecast.forecast_ts.isoformat(),
                'camera_id': forecast.camera_id,
                'model_ver': forecast.model_ver
            }
            
            # Add horizon predictions
            for h in forecast.horizons:
                forecast_dict[f'h:{h.horizon_min}'] = str(h.CI_pred)
            
            # Save with TTL
            pipeline = self.redis.pipeline()
            pipeline.hset(key, mapping=forecast_dict)
            pipeline.expire(key, ttl_sec)
            await pipeline.execute()
            
            logger.debug(f"Saved forecast for camera {forecast.camera_id} ({len(forecast.horizons)} horizons)")
            
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
            
            logger.info(f"Retrieved {len(rows)}/{len(camera_ids)} current states")
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
