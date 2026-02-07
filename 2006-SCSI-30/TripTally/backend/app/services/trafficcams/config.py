"""
Configuration Management
Centralized configuration with validation
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIConfig:
    """API configuration"""
    url: str
    api_key: Optional[str] = None
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(
            url=os.getenv("API_URL", "https://api.data.gov.sg/v1/transport/traffic-images"),
            api_key=os.getenv("X_API_KEY"),
            timeout=int(os.getenv("API_TIMEOUT", "60"))
        )


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str
    port: int
    db: int
    password: Optional[str] = None
    ttl: int = 600

    @classmethod
    def from_env(cls) -> "RedisConfig":
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            ttl=int(os.getenv("REDIS_TTL", "600"))
        )


@dataclass
class ModelConfig:
    """YOLO model configuration"""
    path: str
    img_size: int
    conf_threshold: float
    iou_threshold: float

    @classmethod
    def from_env(cls) -> "ModelConfig":
        return cls(
            path=os.getenv("MODEL_PATH", "models/yolov8n.pt"),
            img_size=int(os.getenv("IMG_SIZE", "640")),
            conf_threshold=float(os.getenv("CONF_THRES", "0.25")),
            iou_threshold=float(os.getenv("IOU_THRES", "0.45"))
        )


@dataclass
class CIConfig:
    """Congestion Index calculation parameters"""
    k_count: float
    k_area: float
    k_motion: float
    w_dens: float
    w_area: float
    w_mrel: float
    w_ciraw: float

    @classmethod
    def from_env(cls) -> "CIConfig":
        return cls(
            k_count=float(os.getenv("K_COUNT", "20")),
            k_area=float(os.getenv("K_AREA", "0.10")),
            k_motion=float(os.getenv("K_MOTION", "8.0")),
            w_dens=float(os.getenv("W_DENS", "0.6")),
            w_area=float(os.getenv("W_AREA", "0.4")),
            w_mrel=float(os.getenv("W_MREL", "0.3")),
            w_ciraw=float(os.getenv("W_CIRAW", "0.7"))
        )


@dataclass
class ProcessingConfig:
    """Processing configuration"""
    loop_interval: int
    max_history: int
    cache_dir: str
    log_level: str
    repository_type: str  # redis, csv, sql
    forecaster_type: str  # simple, ml, auto
    model_dir: str
    data_dir: str
    db_path: str

    @classmethod
    def from_env(cls) -> "ProcessingConfig":
        return cls(
            loop_interval=int(os.getenv("LOOP_INTERVAL", "120")),
            max_history=int(os.getenv("MAX_HISTORY", "60")),
            cache_dir=os.getenv("CACHE_DIR", "./cache"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            repository_type=os.getenv("REPOSITORY_TYPE", "redis"),  # redis, csv, sql
            forecaster_type=os.getenv("FORECASTER_TYPE", "auto"),  # simple, ml, auto
            model_dir=os.getenv("MODEL_DIR", "./models"),
            data_dir=os.getenv("DATA_DIR", "./data"),
            db_path=os.getenv("DB_PATH", "./data/traffic_ci.db")
        )


@dataclass
class Config:
    """Main configuration container"""
    api: APIConfig
    redis: RedisConfig
    model: ModelConfig
    ci: CIConfig
    processing: ProcessingConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load all configuration from environment variables"""
        return cls(
            api=APIConfig.from_env(),
            redis=RedisConfig.from_env(),
            model=ModelConfig.from_env(),
            ci=CIConfig.from_env(),
            processing=ProcessingConfig.from_env()
        )

    def validate(self) -> None:
        """Validate configuration"""
        # Validate ranges
        assert 0 < self.model.conf_threshold < 1, "CONF_THRES must be between 0 and 1"
        assert 0 < self.model.iou_threshold < 1, "IOU_THRES must be between 0 and 1"
        assert self.processing.loop_interval > 0, "LOOP_INTERVAL must be positive"
        assert self.processing.max_history > 0, "MAX_HISTORY must be positive"
