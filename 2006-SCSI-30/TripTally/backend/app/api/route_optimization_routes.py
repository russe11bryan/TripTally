"""
Route Optimization API
FastAPI endpoints for route-based traffic optimization
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from app.services.trafficcams.domain.route_models import Point, LineString
from app.services.trafficcams.domain.geospatial_service import GeospatialService
from app.services.trafficcams.domain.route_optimizer import RouteOptimizationService
from app.services.trafficcams.domain.camera_loader import get_camera_loader
from app.services.trafficcams.factory import ServiceContext
from app.services.trafficcams.config import Config

router = APIRouter(prefix="/api/traffic/route", tags=["Route Optimization"])


# Request/Response Models
class PointRequest(BaseModel):
    """Geographic point in request"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    
    def to_domain(self) -> Point:
        """Convert to domain model"""
        return Point(latitude=self.latitude, longitude=self.longitude)


class RouteOptimizationRequest(BaseModel):
    """Request for route optimization"""
    route_points: List[PointRequest] = Field(
        ..., 
        min_length=2,
        description="Route as list of points (minimum 2 points)"
    )
    estimated_travel_time_minutes: int = Field(
        ...,
        ge=1,
        le=300,
        description="Original estimated travel time in minutes"
    )
    search_radius_km: Optional[float] = Field(
        0.5,
        ge=0.1,
        le=5.0,
        description="Search radius for cameras in km (default: 0.5)"
    )
    forecast_horizon_minutes: Optional[int] = Field(
        120,
        ge=10,
        le=180,
        description="Forecast horizon in minutes (default: 120)"
    )


class CameraInfoResponse(BaseModel):
    """Camera information in response"""
    camera_id: str
    latitude: float
    longitude: float
    distance_to_route_meters: float
    position_on_route: float  # 0.0 to 1.0


class CameraTrafficResponse(BaseModel):
    """Camera traffic info in response"""
    camera_id: str
    current_ci: float
    forecast_ci: float
    timestamp: str


class DepartureOptionResponse(BaseModel):
    """Departure option in response"""
    departure_time: str
    minutes_from_now: int
    average_ci: float
    max_ci: float
    estimated_travel_time_minutes: float
    new_eta: str
    confidence_score: float
    traffic_level: str
    camera_count: int


class RouteOptimizationResponse(BaseModel):
    """Response for route optimization"""
    success: bool
    message: str
    original_eta: str
    original_departure: str
    route_length_km: float
    cameras_found: int
    route_cameras: List[CameraInfoResponse]
    best_departure: DepartureOptionResponse
    alternative_departures: List[DepartureOptionResponse]
    analysis_timestamp: str


# Initialize service (lazy loading)
_service_context: Optional[ServiceContext] = None
_geo_service: Optional[GeospatialService] = None
_optimizer_service: Optional[RouteOptimizationService] = None


def get_optimizer_service() -> RouteOptimizationService:
    """Get or create optimizer service (singleton pattern)"""
    global _service_context, _geo_service, _optimizer_service
    
    if _optimizer_service is None:
        # Load configuration
        config = Config.from_env()
        
        # Create service context (provides repository)
        _service_context = ServiceContext.from_config(config)
        
        # Create geospatial service
        _geo_service = GeospatialService()
        
        # Get camera loader
        camera_loader = get_camera_loader()
        
        # Create optimizer service
        _optimizer_service = RouteOptimizationService(
            repository=_service_context.repository,
            geospatial_service=_geo_service,
            camera_loader=camera_loader
        )
    
    return _optimizer_service


def _classify_traffic_level(ci: float) -> str:
    """Classify CI into human-readable traffic level"""
    if ci < 0.3:
        return "free_flow"
    elif ci < 0.5:
        return "light"
    elif ci < 0.7:
        return "moderate"
    elif ci < 0.9:
        return "heavy"
    else:
        return "severe"


@router.post("/optimize", response_model=RouteOptimizationResponse)
async def optimize_route(request: RouteOptimizationRequest):
    """
    Find optimal departure time for a route based on traffic forecasts
    
    This endpoint:
    1. Finds all traffic cameras along the route
    2. Gets current CI and forecasts for each camera
    3. Analyzes departure times in 10-minute intervals
    4. Returns the best departure time with updated ETA
    
    Returns:
        Route optimization result with best departure time and alternatives
    """
    try:
        # Get optimizer service
        optimizer = get_optimizer_service()
        geo_service = _geo_service
        
        # Convert request to domain models
        route_points = [p.to_domain() for p in request.route_points]
        route = LineString(points=route_points)
        
        # Calculate route length
        route_length = geo_service.calculate_route_length(route)
        
        # Perform optimization
        result = optimizer.optimize_route(
            route=route,
            original_eta_minutes=request.estimated_travel_time_minutes,
            search_radius_km=request.search_radius_km,
            forecast_horizon_minutes=request.forecast_horizon_minutes
        )
        
        # Convert to response format
        response = RouteOptimizationResponse(
            success=True,
            message=f"Found {len(result.route_cameras)} cameras along route",
            original_eta=result.original_eta.isoformat(),
            original_departure=result.original_departure.isoformat(),
            route_length_km=round(route_length, 2),
            cameras_found=len(result.route_cameras),
            route_cameras=[
                CameraInfoResponse(
                    camera_id=cam.camera_id,
                    latitude=cam.latitude,
                    longitude=cam.longitude,
                    distance_to_route_meters=round(cam.distance_to_route, 1),
                    position_on_route=round(cam.position_on_route, 3)
                )
                for cam in result.route_cameras
            ],
            best_departure=DepartureOptionResponse(
                departure_time=result.best_departure.departure_time.isoformat(),
                minutes_from_now=result.best_departure.minutes_from_now,
                average_ci=result.best_departure.average_ci,
                max_ci=result.best_departure.max_ci,
                estimated_travel_time_minutes=result.best_departure.estimated_travel_time_minutes,
                new_eta=result.best_departure.new_eta.isoformat(),
                confidence_score=result.best_departure.confidence_score,
                traffic_level=_classify_traffic_level(result.best_departure.average_ci),
                camera_count=len(result.best_departure.camera_forecasts)
            ),
            alternative_departures=[
                DepartureOptionResponse(
                    departure_time=opt.departure_time.isoformat(),
                    minutes_from_now=opt.minutes_from_now,
                    average_ci=opt.average_ci,
                    max_ci=opt.max_ci,
                    estimated_travel_time_minutes=opt.estimated_travel_time_minutes,
                    new_eta=opt.new_eta.isoformat(),
                    confidence_score=opt.confidence_score,
                    traffic_level=_classify_traffic_level(opt.average_ci),
                    camera_count=len(opt.camera_forecasts)
                )
                for opt in result.alternative_departures
            ],
            analysis_timestamp=result.analysis_timestamp.isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Route optimization failed: {str(e)}"
        )


@router.get("/cameras-along-route")
async def get_cameras_along_route(
    points: str = Query(
        ...,
        description="Route points as comma-separated lat,lon pairs (e.g., '1.3521,103.8198,1.3621,103.8298')"
    ),
    radius_km: float = Query(
        0.5,
        ge=0.1,
        le=5.0,
        description="Search radius in kilometers"
    )
):
    """
    Get all cameras within radius of a route (lightweight endpoint)
    
    Args:
        points: Route as comma-separated lat,lon pairs
        radius_km: Search radius
        
    Returns:
        List of cameras along route
    """
    try:
        # Parse points
        coords = [float(x) for x in points.split(',')]
        if len(coords) % 2 != 0:
            raise ValueError("Points must be pairs of lat,lon")
        
        route_points = [
            Point(latitude=coords[i], longitude=coords[i+1])
            for i in range(0, len(coords), 2)
        ]
        
        if len(route_points) < 2:
            raise ValueError("Route must have at least 2 points")
        
        # Get services
        optimizer = get_optimizer_service()
        geo_service = _geo_service
        
        # Load all cameras from static file
        camera_loader = get_camera_loader()
        cameras = camera_loader.load_cameras()
        
        # Find cameras along route
        route = LineString(points=route_points)
        route_cameras = geo_service.find_cameras_along_route(
            route, cameras, radius_km
        )
        
        return {
            "success": True,
            "route_points": len(route_points),
            "cameras_found": len(route_cameras),
            "cameras": [
                {
                    "camera_id": cam.camera_id,
                    "latitude": cam.latitude,
                    "longitude": cam.longitude,
                    "distance_to_route_meters": round(cam.distance_to_route, 1),
                    "position_on_route": round(cam.position_on_route, 3)
                }
                for cam in route_cameras
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find cameras: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        optimizer = get_optimizer_service()
        repo_healthy = optimizer.repository.health_check()
        
        return {
            "status": "healthy" if repo_healthy else "degraded",
            "repository": optimizer.repository.get_repository_name(),
            "repository_healthy": repo_healthy
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
