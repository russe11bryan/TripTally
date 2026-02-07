"""
Simple Traffic Camera API Routes
Minimal implementation for CI now and forecast endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import redis
import os

# Initialize router
router = APIRouter(prefix="/api/cameras", tags=["Traffic Cameras"])

# Redis client
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)


def _fresh(ts_str: str, max_age_sec: int = 300):
    """
    Check if timestamp is fresh (< max_age_sec seconds old)
    Raises HTTPException 503 if stale
    """
    ts = datetime.fromisoformat(ts_str)
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    if age > max_age_sec:
        raise HTTPException(
            status_code=503,
            detail=f"Data is stale (age: {age:.0f}s)"
        )


@router.get("/{cid}/now")
def now(cid: str):
    """
    Get current CI state for camera
    
    Returns:
        - timestamp
        - camera_id
        - CI (congestion index)
        - veh_count (vehicle count)
        - area_ratio
        - motion
        - model_ver
    """
    d = r.hgetall(f"ci:now:{cid}")
    if not d:
        raise HTTPException(404, "not found")
    
    _fresh(d["ts"])
    
    return {
        "ts": d["ts"],
        "camera_id": cid,
        "CI": float(d["CI"]),
        "veh_count": int(d["veh_count"]),
        "area_ratio": float(d["area_ratio"]),
        "motion": float(d["motion"]),
        "model_ver": d["model_ver"]
    }


@router.get("/{cid}/forecast")
def forecast(cid: str):
    """
    Get CI forecast for camera
    
    Returns predictions at 2, 4, 6, ..., 120 minute horizons
    
    Returns:
        - timestamp
        - camera_id
        - horizons_min (list of forecast horizons in minutes)
        - CI_forecast (list of predicted CI values)
        - model_ver
    """
    d = r.hgetall(f"ci:fcst:{cid}")
    if not d:
        raise HTTPException(404, "not found")
    
    _fresh(d["ts"], 600)  # 10 minute freshness for forecasts
    
    horizons = list(range(2, 121, 2))
    
    return {
        "ts": d["ts"],
        "camera_id": cid,
        "horizons_min": horizons,
        "CI_forecast": [float(d.get(f"h:{h}", "nan")) for h in horizons],
        "model_ver": d["model_ver"]
    }


@router.get("/health")
def health():
    """Health check endpoint"""
    try:
        r.ping()
        return {"status": "healthy", "service": "traffic_cameras"}
    except Exception as e:
        raise HTTPException(503, f"Redis unavailable: {e}")
