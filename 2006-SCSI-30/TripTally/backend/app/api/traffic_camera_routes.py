"""
Traffic Camera API Controller
Part of the Controller layer in MVC - handles HTTP requests/responses
"""

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.traffic_camera import (
    NowDTO,
    ForecastDTO,
    CameraListDTO,
    Camera
)
from app.ports.traffic_camera_repo import ITrafficCameraRepo
from app.api.deps import get_traffic_camera_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cameras", tags=["Traffic Cameras"])


@router.get("/", response_model=CameraListDTO)
async def list_cameras(
    repo: ITrafficCameraRepo = Depends(get_traffic_camera_repo)
):
    """
    List all cameras with current CI state
    
    Returns current traffic state for all cameras
    """
    try:
        # Get all current states
        rows = await repo.get_all_now()
        
        # Get camera metadata
        cameras_meta = await repo.get_all_cameras()
        camera_map = {cam.camera_id: cam for cam in cameras_meta}
        
        # Convert to DTOs
        now_dtos = []
        for row in rows:
            camera = camera_map.get(row.camera_id)
            dto = NowDTO.from_canonical(row, camera)
            now_dtos.append(dto)
        
        return CameraListDTO(
            cameras=now_dtos,
            total=len(now_dtos),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error listing cameras: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{camera_id}/now", response_model=NowDTO)
async def get_camera_now(
    camera_id: str,
    repo: ITrafficCameraRepo = Depends(get_traffic_camera_repo)
):
    """
    Get current CI state for a specific camera
    
    Returns:
        - Current congestion index
        - Vehicle count
        - Timestamp
        - Freshness indicator
    
    Raises:
        - 404 if camera not found
        - 503 if data is stale (> 5 minutes old)
    """
    try:
        # Get current state
        row = await repo.get_now(camera_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Camera {camera_id} not found or no data available"
            )
        
        # Get camera metadata
        camera = await repo.get_camera(camera_id)
        
        # Convert to DTO
        dto = NowDTO.from_canonical(row, camera)
        
        # Check freshness
        if not dto.is_fresh:
            logger.warning(f"Stale data for camera {camera_id}")
            raise HTTPException(
                status_code=503,
                detail=f"Data for camera {camera_id} is stale (last update: {dto.ts})"
            )
        
        return dto
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting now for camera {camera_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{camera_id}/forecast", response_model=ForecastDTO)
async def get_camera_forecast(
    camera_id: str,
    repo: ITrafficCameraRepo = Depends(get_traffic_camera_repo)
):
    """
    Get CI forecast for a specific camera
    
    Returns predictions for the next 2, 5, 10, 15, 30, 60, and 120 minutes
    
    Raises:
        - 404 if camera not found
        - 503 if forecast is stale (> 5 minutes old)
    """
    try:
        # Get forecast
        forecast = await repo.get_forecast(camera_id)
        if not forecast:
            raise HTTPException(
                status_code=404,
                detail=f"Forecast for camera {camera_id} not found"
            )
        
        # Get camera metadata
        camera = await repo.get_camera(camera_id)
        
        # Convert to DTO
        dto = ForecastDTO.from_forecast_vector(forecast, camera)
        
        # Check freshness
        if not dto.is_fresh:
            logger.warning(f"Stale forecast for camera {camera_id}")
            raise HTTPException(
                status_code=503,
                detail=f"Forecast for camera {camera_id} is stale (last update: {dto.forecast_ts})"
            )
        
        return dto
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast for camera {camera_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{camera_id}/metadata", response_model=Camera)
async def get_camera_metadata(
    camera_id: str,
    repo: ITrafficCameraRepo = Depends(get_traffic_camera_repo)
):
    """
    Get camera metadata (location, etc.)
    
    Returns camera information without current state
    """
    try:
        camera = await repo.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=404,
                detail=f"Camera {camera_id} not found"
            )
        
        return camera
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata for camera {camera_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=dict)
async def health_check(
    repo: ITrafficCameraRepo = Depends(get_traffic_camera_repo)
):
    """
    Health check endpoint
    
    Verifies that the repository (Redis) is accessible
    """
    try:
        is_healthy = await repo.health_check()
        if not is_healthy:
            raise HTTPException(
                status_code=503,
                detail="Traffic camera service unhealthy"
            )
        
        return {
            "status": "healthy",
            "service": "traffic_cameras",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unavailable")
