"""
CI Processing Service
Main orchestrator that coordinates all components
"""

import io
import time
from datetime import datetime, timezone
from PIL import Image
import numpy as np
import cv2

from .config import Config
from .api_client import TrafficCameraAPIClient, CameraImageData
from .data_repository import DataRepository
from .forecasting_strategy import ForecastingStrategy
from .factory import ServiceContext, RepositoryFactory, ForecasterFactory, RepositoryType, ForecasterType
from .ci_calculator import CICalculator
from .motion_detector import MotionDetector
from .yolo import YOLO
from .models import Camera, DetectionResult, CIState
from .logger import get_logger

logger = get_logger("ci_service")


class CIProcessingService:
    """Main service for CI calculation and forecasting"""
    
    def __init__(
        self, 
        config: Config,
        repo_type: str = None,
        forecaster_type: str = None
    ):
        self.config = config
        
        # Initialize components
        logger.info("Initializing CI Processing Service")
        self.api_client = TrafficCameraAPIClient(config.api)
        self.ci_calculator = CICalculator(config.ci)
        self.motion_detector = MotionDetector(config.processing.cache_dir)
        
        # Use factory pattern to create repository and forecaster
        # This allows easy switching between implementations
        repo_type = repo_type or getattr(config.processing, 'repository_type', 'redis')
        forecaster_type = forecaster_type or getattr(config.processing, 'forecaster_type', 'auto')
        
        logger.info(f"Creating service with repository={repo_type}, forecaster={forecaster_type}")
        self.context = ServiceContext.from_config(config, repo_type, forecaster_type)
        self.repository = self.context.repository
        self.forecaster = self.context.forecaster
        
        # Initialize YOLO model
        logger.info(f"Loading YOLO model from {config.model.path}")
        self.yolo = YOLO(
            path=config.model.path,
            img_size=config.model.img_size,
            conf=config.model.conf_threshold,
            iou=config.model.iou_threshold
        )
        logger.info("YOLO model loaded successfully")
    
    def check_health(self) -> bool:
        """Health check for all dependencies"""
        try:
            if not self.repository.ping():
                logger.error("Redis health check failed")
                return False
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def process_camera(self, camera_data: CameraImageData, timestamp: datetime) -> bool:
        """
        Process single camera: download, detect, calculate CI, forecast
        
        Args:
            camera_data: Camera information and image URL
            timestamp: Timestamp from API
            
        Returns:
            True if successful, False otherwise
        """
        camera_id = camera_data.camera_id
        
        try:
            # Download image
            t_dl_start = time.perf_counter()
            image_bytes = self.api_client.download_image(camera_data.image_url)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_rgb = np.array(image)
            t_dl = (time.perf_counter() - t_dl_start) * 1000
            
            # Run YOLO detection
            t_inf_start = time.perf_counter()
            bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            boxes, scores, class_ids, ((r_w, r_h), dw, dh) = self.yolo.infer(bgr)
            
            # Convert to native coordinates
            boxes = self.yolo.to_native(
                boxes.copy(),
                camera_data.image_width,
                camera_data.image_height,
                ((r_w, r_h), dw, dh),
                dw,
                dh
            )
            t_inf = (time.perf_counter() - t_inf_start) * 1000
            
            # Create detection result
            detection = DetectionResult(
                boxes=boxes.tolist(),
                scores=scores.tolist(),
                class_ids=class_ids.tolist(),
                vehicle_count=len(boxes),
                weighted_count=0.0,  # Will be calculated
                area_ratio=0.0,  # Will be calculated
                inference_time_ms=t_inf
            )
            
            # Calculate metrics
            weighted_count = self.ci_calculator.calculate_weighted_count(detection)
            img_area = camera_data.image_width * camera_data.image_height
            area_ratio = self.ci_calculator.calculate_area_ratio(detection, img_area)
            
            # Calculate motion
            motion_score = self.motion_detector.calculate_motion(camera_id, image_rgb)
            
            # Calculate CI
            ci = self.ci_calculator.calculate_ci(weighted_count, area_ratio, motion_score)
            
            # Calculate temporal features
            temporal = self.ci_calculator.calculate_temporal_features(timestamp)
            
            # Create CI state
            ci_state = CIState(
                camera_id=camera_id,
                timestamp=timestamp,
                ci=ci,
                vehicle_count=detection.vehicle_count,
                weighted_count=weighted_count,
                area_ratio=area_ratio,
                motion_score=motion_score,
                minute_of_day=temporal[0],
                hour=temporal[1],
                day_of_week=temporal[2],
                is_weekend=temporal[3],
                sin_t_h=temporal[4],
                cos_t_h=temporal[5],
                img_width=camera_data.image_width,
                img_height=camera_data.image_height
            )
            
            # Save to Redis
            self.repository.save_ci_state(ci_state)
            
            # Generate and save forecast
            self.forecaster.add_observation(camera_id, timestamp, ci)
            forecast = self.forecaster.generate_forecast(ci_state)
            self.repository.save_forecast(forecast)
            
            # Save camera metadata
            camera = Camera(
                camera_id=camera_id,
                latitude=camera_data.latitude,
                longitude=camera_data.longitude,
                image_url=camera_data.image_url
            )
            self.repository.save_camera_metadata(camera)
            
            # Log success
            logger.info(
                f"cam={camera_id} "
                f"dl={t_dl:.1f}ms inf={t_inf:.1f}ms "
                f"veh={detection.vehicle_count} "
                f"CI={ci:.3f} "
                f"motion={motion_score:.2f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing camera {camera_id}: {e}", exc_info=True)
            return False
    
    def process_all_cameras(self) -> dict:
        """
        Process all cameras from API
        
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.perf_counter()
        
        try:
            # Fetch camera data from API
            timestamp_str, cameras = self.api_client.fetch_cameras()
            
            if not cameras:
                logger.warning("No cameras returned from API")
                return {"success": False, "error": "No cameras available"}
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            
            logger.info(f"Processing {len(cameras)} cameras at {timestamp_str}")
            
            # Process each camera
            success_count = 0
            error_count = 0
            
            for camera_data in cameras:
                if self.process_camera(camera_data, timestamp):
                    success_count += 1
                else:
                    error_count += 1
            
            elapsed = (time.perf_counter() - start_time) * 1000
            
            # Log summary
            logger.info(
                f"Processing complete: "
                f"success={success_count}/{len(cameras)} "
                f"errors={error_count} "
                f"time={elapsed:.0f}ms"
            )
            
            return {
                "success": True,
                "timestamp": timestamp_str,
                "total": len(cameras),
                "processed": success_count,
                "errors": error_count,
                "elapsed_ms": elapsed
            }
            
        except Exception as e:
            logger.error(f"Error in process_all_cameras: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def run_loop(self) -> None:
        """Run continuous processing loop"""
        iteration = 0
        interval = self.config.processing.loop_interval
        
        logger.info(f"Starting processing loop (interval={interval}s)")
        
        while True:
            iteration += 1
            logger.info(f"=== Iteration {iteration} ===")
            
            try:
                stats = self.process_all_cameras()
                if not stats.get("success"):
                    logger.error(f"Iteration failed: {stats.get('error')}")
            except Exception as e:
                logger.error(f"Iteration error: {e}", exc_info=True)
            
            logger.info(f"Sleeping {interval}s until next iteration...")
            time.sleep(interval)
    
    def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("Shutting down CI Processing Service")
        try:
            self.api_client.close()
            self.repository.close()
            logger.info("Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
