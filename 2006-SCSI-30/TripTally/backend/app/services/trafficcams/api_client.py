"""
Traffic Camera API Client
External API interaction layer
"""

import requests
from typing import List, Dict, Any
from dataclasses import dataclass

from .config import APIConfig
from .models import Camera
from .logger import get_logger

logger = get_logger("api_client")


@dataclass
class CameraImageData:
    """Raw camera image data from API"""
    camera_id: str
    image_url: str
    latitude: float
    longitude: float
    image_width: int
    image_height: int


class TrafficCameraAPIClient:
    """Client for Singapore LTA Traffic Camera API"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        if config.api_key:
            self.session.headers.update({"X-Api-Key": config.api_key})
        self.session.headers.update({"Accept": "application/json"})
    
    def fetch_cameras(self) -> tuple[str, List[CameraImageData]]:
        """
        Fetch camera data from API
        
        Returns:
            Tuple of (timestamp, list of camera data)
        """
        try:
            logger.info("Fetching camera data from API")
            response = self.session.get(
                self.config.url,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                logger.warning("No items in API response")
                return "", []
            
            item = items[0]
            timestamp = item.get("timestamp", "")
            cameras_raw = item.get("cameras", [])
            
            cameras = []
            for cam in cameras_raw:
                try:
                    camera_data = CameraImageData(
                        camera_id=str(cam.get("camera_id")),
                        image_url=cam.get("image"),
                        latitude=cam.get("location", {}).get("latitude", 0.0),
                        longitude=cam.get("location", {}).get("longitude", 0.0),
                        image_width=int(cam.get("image_metadata", {}).get("width", 0) or 0),
                        image_height=int(cam.get("image_metadata", {}).get("height", 0) or 0)
                    )
                    cameras.append(camera_data)
                except Exception as e:
                    logger.error(f"Error parsing camera data: {e}")
                    continue
            
            logger.info(f"Fetched {len(cameras)} cameras at {timestamp}")
            return timestamp, cameras
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching cameras: {e}")
            raise
    
    def download_image(self, url: str) -> bytes:
        """Download camera image"""
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            raise
    
    def close(self) -> None:
        """Close session"""
        self.session.close()
