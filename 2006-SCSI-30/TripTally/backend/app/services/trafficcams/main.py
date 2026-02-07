"""
Main Entry Point
Application startup and lifecycle management
"""

import sys
import signal
from pathlib import Path

from .config import Config
from .logger import setup_logging, get_logger
from .service import CIProcessingService


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = get_logger("main")
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main application entry point"""
    # Load configuration
    try:
        config = Config.from_env()
        config.validate()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(
        log_level=config.processing.log_level,
        log_dir=config.processing.cache_dir + "/../logs"
    )
    logger.info("=" * 60)
    logger.info("TripTally CI Processing Service")
    logger.info("=" * 60)
    
    # Log configuration
    logger.info(f"Model: {config.model.path}")
    logger.info(f"Image Size: {config.model.img_size}")
    logger.info(f"Confidence: {config.model.conf_threshold}")
    logger.info(f"IOU: {config.model.iou_threshold}")
    logger.info(f"Redis: {config.redis.host}:{config.redis.port} (DB {config.redis.db})")
    logger.info(f"Loop Interval: {config.processing.loop_interval}s")
    logger.info(f"Max History: {config.processing.max_history} observations")
    logger.info("=" * 60)
    
    # Create cache directory
    Path(config.processing.cache_dir).mkdir(parents=True, exist_ok=True)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize service
    try:
        service = CIProcessingService(config)
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}", exc_info=True)
        sys.exit(1)
    
    # Health check
    if not service.check_health():
        logger.error("Health check failed, exiting")
        sys.exit(1)
    
    # Run service
    try:
        service.run_loop()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        service.shutdown()
    
    logger.info("Service stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
