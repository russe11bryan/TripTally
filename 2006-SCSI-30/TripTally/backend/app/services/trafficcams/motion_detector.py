"""
Motion Detector
Calculates motion score using frame differencing
"""

import cv2
import numpy as np
from pathlib import Path

from .logger import get_logger

logger = get_logger("motion_detector")


class MotionDetector:
    """Detect motion between consecutive frames"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir) / "prev_frames"
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Motion detector cache directory created: {self.cache_dir}")
        except PermissionError as e:
            logger.error(f"Permission denied creating cache directory: {self.cache_dir}")
            logger.error(f"Please ensure the directory exists and has proper permissions")
            raise RuntimeError(f"Cannot create cache directory at {self.cache_dir}: {e}") from e
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise
    
    def calculate_motion(self, camera_id: str, image_rgb: np.ndarray) -> float:
        """
        Calculate motion score using frame differencing
        
        Args:
            camera_id: Unique camera identifier
            image_rgb: Current frame in RGB format
            
        Returns:
            Motion score (0-10 scale)
        """
        try:
            prev_path = self.cache_dir / f"{camera_id}.jpg"
            
            # Resize to fixed width for consistent comparison
            h, w = image_rgb.shape[:2]
            scale = 320.0 / max(1, w)
            small = cv2.resize(
                image_rgb,
                (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_AREA
            )
            
            # Convert to grayscale
            gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
            
            motion_score = 0.0
            
            # Compare with previous frame if exists
            if prev_path.exists():
                try:
                    prev = cv2.imdecode(
                        np.fromfile(str(prev_path), dtype=np.uint8),
                        cv2.IMREAD_GRAYSCALE
                    )
                    
                    if prev is not None and prev.shape == gray.shape:
                        # Calculate absolute difference
                        diff = cv2.absdiff(gray, prev)
                        
                        # Use median difference as motion score
                        # Scale to 0-10 range
                        motion_score = float(np.median(diff)) / 255.0 * 10.0
                        
                except Exception as e:
                    logger.debug(f"Error loading previous frame for {camera_id}: {e}")
            
            # Save current frame for next comparison
            _, encoded = cv2.imencode('.jpg', gray, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            encoded.tofile(str(prev_path))
            
            return motion_score
            
        except Exception as e:
            logger.error(f"Motion detection failed for {camera_id}: {e}")
            return 0.0
