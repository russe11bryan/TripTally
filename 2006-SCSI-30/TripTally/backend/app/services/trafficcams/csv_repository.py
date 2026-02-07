"""
CSV Repository Implementation
Implements DataRepository interface for CSV file storage
"""

import csv
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from threading import Lock

from .data_repository import DataRepository
from .models import CIState, CIForecast, Camera
from .logger import get_logger

logger = get_logger("csv_repo")


class CSVRepository(DataRepository):
    """CSV implementation of DataRepository"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.ci_states_file = self.base_dir / "ci_states.csv"
        self.forecasts_file = self.base_dir / "forecasts.csv"
        self.cameras_file = self.base_dir / "cameras.csv"
        
        # Thread safety
        self.lock = Lock()
        
        # Initialize files
        self._initialize_files()
        
        logger.info(f"CSV Repository initialized at {self.base_dir}")
    
    def _initialize_files(self):
        """Create CSV files with headers if they don't exist"""
        # CI states file
        if not self.ci_states_file.exists():
            with open(self.ci_states_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'camera_id', 'ci', 'vehicle_count', 
                    'weighted_count', 'area_ratio', 'motion_score',
                    'img_width', 'img_height', 'minute_of_day', 'hour',
                    'day_of_week', 'is_weekend', 'sin_t_h', 'cos_t_h',
                    'model_version'
                ])
        
        # Forecasts file
        if not self.forecasts_file.exists():
            with open(self.forecasts_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'camera_id', 'current_ci', 'forecast_time',
                    'forecasts_json', 'model_version'
                ])
        
        # Cameras file
        if not self.cameras_file.exists():
            with open(self.cameras_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['camera_id', 'latitude', 'longitude'])
    
    def save_ci_state(self, state: CIState) -> bool:
        """Save current CI state"""
        try:
            with self.lock:
                with open(self.ci_states_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        state.timestamp.isoformat(),
                        state.camera_id,
                        state.ci,
                        state.vehicle_count,
                        state.weighted_count,
                        state.area_ratio,
                        state.motion_score,
                        state.img_width,
                        state.img_height,
                        state.minute_of_day,
                        state.hour,
                        state.day_of_week,
                        state.is_weekend,
                        state.sin_t_h,
                        state.cos_t_h,
                        state.model_version
                    ])
            logger.debug(f"Saved CI state for camera {state.camera_id} to CSV")
            return True
        except Exception as e:
            logger.error(f"Failed to save CI state to CSV: {e}")
            return False
    
    def get_ci_state(self, camera_id: str) -> Optional[CIState]:
        """Retrieve latest CI state for camera"""
        try:
            with self.lock:
                # Read file backwards to get latest state
                with open(self.ci_states_file, 'r') as f:
                    reader = csv.DictReader(f)
                    states = [row for row in reader if row['camera_id'] == camera_id]
                    
                    if not states:
                        return None
                    
                    # Return most recent (last in file)
                    latest = states[-1]
                    return latest  # Return as dict for now
        except Exception as e:
            logger.error(f"Failed to get CI state from CSV: {e}")
            return None
    
    def save_forecast(self, forecast: CIForecast) -> bool:
        """Save forecast"""
        try:
            with self.lock:
                with open(self.forecasts_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        forecast.camera_id,
                        forecast.current_ci,
                        forecast.forecast_time.isoformat(),
                        json.dumps([f.__dict__ for f in forecast.forecasts]),
                        forecast.model_version
                    ])
            logger.debug(f"Saved forecast for camera {forecast.camera_id} to CSV")
            return True
        except Exception as e:
            logger.error(f"Failed to save forecast to CSV: {e}")
            return False
    
    def get_forecast(self, camera_id: str) -> Optional[CIForecast]:
        """Retrieve latest forecast for camera"""
        try:
            with self.lock:
                with open(self.forecasts_file, 'r') as f:
                    reader = csv.DictReader(f)
                    forecasts = [row for row in reader if row['camera_id'] == camera_id]
                    
                    if not forecasts:
                        return None
                    
                    # Return most recent
                    return forecasts[-1]  # Return as dict for now
        except Exception as e:
            logger.error(f"Failed to get forecast from CSV: {e}")
            return None
    
    def save_camera_metadata(self, camera: Camera) -> bool:
        """Save camera metadata"""
        try:
            with self.lock:
                # Check if camera already exists
                existing = []
                if self.cameras_file.exists():
                    with open(self.cameras_file, 'r') as f:
                        reader = csv.DictReader(f)
                        existing = [row for row in reader if row['camera_id'] != camera.camera_id]
                
                # Rewrite file with updated camera
                with open(self.cameras_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['camera_id', 'latitude', 'longitude'])
                    
                    for row in existing:
                        writer.writerow([row['camera_id'], row['latitude'], row['longitude']])
                    
                    writer.writerow([camera.camera_id, camera.latitude, camera.longitude])
            
            logger.debug(f"Saved camera metadata for {camera.camera_id} to CSV")
            return True
        except Exception as e:
            logger.error(f"Failed to save camera metadata to CSV: {e}")
            return False
    
    def get_camera_metadata(self, camera_id: str) -> Optional[Camera]:
        """Retrieve camera metadata"""
        try:
            with self.lock:
                with open(self.cameras_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['camera_id'] == camera_id:
                            return row  # Return as dict for now
            return None
        except Exception as e:
            logger.error(f"Failed to get camera metadata from CSV: {e}")
            return None
    
    def list_cameras(self) -> List[str]:
        """List all camera IDs"""
        try:
            with self.lock:
                with open(self.cameras_file, 'r') as f:
                    reader = csv.DictReader(f)
                    return [row['camera_id'] for row in reader]
        except Exception as e:
            logger.error(f"Failed to list cameras from CSV: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if repository is healthy"""
        try:
            return (
                self.ci_states_file.exists() and
                self.forecasts_file.exists() and
                self.cameras_file.exists()
            )
        except Exception:
            return False
    
    def get_repository_name(self) -> str:
        """Return name of the repository implementation"""
        return "CSV"
