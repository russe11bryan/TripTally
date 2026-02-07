"""
Camera Data Loader
Loads camera metadata from static JSON file
"""

import json
from pathlib import Path
from typing import List, Optional
from ..models import Camera
from ..logger import get_logger

logger = get_logger("camera_loader")


class CameraDataLoader:
    """Loads camera data from JSON file"""
    
    DEFAULT_CAMERA_FILE = Path(__file__).parent.parent / "train" / "data" / "cam_id_lat_lon.json"
    
    def __init__(self, camera_file: Optional[Path] = None):
        """
        Initialize camera loader
        
        Args:
            camera_file: Path to camera JSON file (default: train/data/cam_id_lat_lon.json)
        """
        self.camera_file = camera_file or self.DEFAULT_CAMERA_FILE
        self._cameras: Optional[List[Camera]] = None
    
    def load_cameras(self) -> List[Camera]:
        """
        Load all cameras from JSON file
        
        Returns:
            List of Camera objects
        """
        if self._cameras is not None:
            return self._cameras
        
        try:
            logger.info(f"Loading cameras from {self.camera_file}")
            
            with open(self.camera_file, 'r') as f:
                data = json.load(f)
            
            cameras = []
            for item in data:
                camera = Camera(
                    camera_id=str(item['cam_id']),
                    latitude=float(item['lat']),
                    longitude=float(item['lon']),
                    image_url=None  # Not available in static file
                )
                cameras.append(camera)
            
            self._cameras = cameras
            logger.info(f"Loaded {len(cameras)} cameras")
            return cameras
            
        except FileNotFoundError:
            logger.error(f"Camera file not found: {self.camera_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in camera file: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing required field in camera data: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load cameras: {e}")
            raise
    
    def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """
        Get specific camera by ID
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Camera object or None if not found
        """
        cameras = self.load_cameras()
        for camera in cameras:
            if camera.camera_id == camera_id:
                return camera
        return None
    
    def get_camera_ids(self) -> List[str]:
        """
        Get list of all camera IDs
        
        Returns:
            List of camera ID strings
        """
        cameras = self.load_cameras()
        return [cam.camera_id for cam in cameras]


# Singleton instance
_camera_loader: Optional[CameraDataLoader] = None


def get_camera_loader() -> CameraDataLoader:
    """Get singleton camera loader instance"""
    global _camera_loader
    if _camera_loader is None:
        _camera_loader = CameraDataLoader()
    return _camera_loader
