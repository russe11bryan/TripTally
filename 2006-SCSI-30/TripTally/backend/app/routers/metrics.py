from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..metrics.get_metrics import get_route_metrics
from ..metrics.lta_carpark_full_data import get_nearby_carparks

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"]
)

@router.get("/driving")
async def get_driving_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get driving metrics for a route"""
    if origin_lat is None or origin_lng is None:
        # If origin not provided, use reasonable defaults
        origin_lat = 1.3521  # Singapore center
        origin_lng = 103.8198
    
    metrics = get_route_metrics(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        mode='driving'
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/public-transport")
async def get_pt_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get public transport metrics for a route"""
    if origin_lat is None or origin_lng is None:
        # If origin not provided, use reasonable defaults
        origin_lat = 1.3521  # Singapore center
        origin_lng = 103.8198
    
    metrics = get_route_metrics(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        mode='transit'
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/walking")
async def get_walking_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get walking metrics for a route"""
    if origin_lat is None or origin_lng is None:
        # If origin not provided, use reasonable defaults
        origin_lat = 1.3521  # Singapore center
        origin_lng = 103.8198
    
    metrics = get_route_metrics(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        mode='walking'
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/cycling")
async def get_cycling_metrics(
    origin_lat: Optional[float] = Query(None),
    origin_lng: Optional[float] = Query(None),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
):
    """Get cycling metrics for a route"""
    if origin_lat is None or origin_lng is None:
        # If origin not provided, use reasonable defaults
        origin_lat = 1.3521  # Singapore center
        origin_lng = 103.8198
    
    metrics = get_route_metrics(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
        mode='bicycling'
    )
    
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return metrics

@router.get("/carparks")
async def get_carparks(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: Optional[int] = Query(1500)
):
    """Get nearby carparks within a radius"""
    carparks = get_nearby_carparks(latitude, longitude, radius_meters)
    return carparks