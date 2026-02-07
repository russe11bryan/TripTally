"""
Departure Time Optimization API
FastAPI endpoints for finding best departure time based on traffic forecasts

Architecture: RESTful API with proper request/response models
Design Pattern: DTO (Data Transfer Objects) for API layer
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from app.services.trafficcams.domain.route_models import Point
from app.services.trafficcams.domain.geospatial_service import GeospatialService
from app.services.trafficcams.domain.departure_time_optimizer import DepartureTimeOptimizer
from app.services.trafficcams.domain.camera_loader import get_camera_loader
from app.services.trafficcams.factory import ServiceContext
from app.services.trafficcams.config import Config
from app.services.trafficcams.logger import get_logger

logger = get_logger("departure_api")

router = APIRouter(prefix="/api/traffic/departure", tags=["Departure Time Optimization"])


# Request Models (DTOs)
class RoutePointRequest(BaseModel):
    """Point in a route"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    def to_domain(self) -> Point:
        """Convert to domain model"""
        return Point(latitude=self.latitude, longitude=self.longitude)


class OptimalDepartureRequest(BaseModel):
    """Request for optimal departure time"""
    route_points: List[RoutePointRequest] = Field(
        ...,
        min_length=2,
        description="Route as list of lat/lon points"
    )
    original_eta_minutes: int = Field(
        ...,
        ge=1,
        le=300,
        description="Original estimated travel time in minutes"
    )
    search_radius_km: float = Field(
        0.5,
        ge=0.1,
        le=5.0,
        description="Search radius for cameras (default: 0.5km)"
    )
    forecast_horizon_minutes: int = Field(
        120,
        ge=10,
        le=180,
        description="Forecast horizon (default: 120 minutes)"
    )


# Response Models (DTOs)
class OptimalDepartureResponse(BaseModel):
    """Response with optimal departure time"""
    # Recommendation
    best_time_minutes_from_now: int = Field(
        description="Best time to leave (minutes from now)"
    )
    best_departure_time: str = Field(
        description="Best departure time (ISO 8601 format)"
    )
    
    # ETA comparison
    original_eta_minutes: int = Field(
        description="Original ETA in minutes"
    )
    current_eta_minutes: int = Field(
        description="ETA if leaving now"
    )
    optimized_eta_minutes: int = Field(
        description="ETA if leaving at optimal time"
    )
    time_saved_minutes: int = Field(
        description="Time saved by waiting (can be negative)"
    )
    
    # Traffic analysis
    current_average_ci: float = Field(
        description="Current average congestion index"
    )
    optimal_average_ci: float = Field(
        description="Optimal average congestion index"
    )
    cameras_analyzed: int = Field(
        description="Number of cameras analyzed"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in recommendation (0.0 to 1.0)"
    )
    
    # Human-readable message
    recommendation_text: str = Field(
        description="Human-readable recommendation"
    )


@router.post("/optimize", response_model=OptimalDepartureResponse)
async def optimize_departure_time(request: OptimalDepartureRequest):
    """
    Find the optimal departure time based on traffic forecasts
    
    This endpoint:
    1. Finds cameras near the route
    2. Gets current CI and forecasts for all cameras
    3. Analyzes traffic conditions at 2-minute intervals
    4. Returns the time with minimum congestion
    5. Calculates adjusted ETA based on traffic
    
    Returns:
        Optimal departure time and updated ETA
    """
    try:
        logger.info(
            f"Optimizing departure: {len(request.route_points)} points, "
            f"ETA={request.original_eta_minutes}min"
        )
        
        # Convert request to domain models
        route_points = [p.to_domain() for p in request.route_points]
        
        # Get dependencies (Factory Pattern)
        config = Config.from_env()
        service_context = ServiceContext.from_config(config)
        repository = service_context.repository
        geospatial = GeospatialService()
        camera_loader = get_camera_loader()
        
        # Create optimizer service
        optimizer = DepartureTimeOptimizer(
            repository=repository,
            geospatial_service=geospatial,
            camera_loader=camera_loader
        )
        
        # Find optimal departure time
        result = optimizer.find_optimal_departure(
            route_points=route_points,
            original_eta_minutes=request.original_eta_minutes,
            search_radius_km=request.search_radius_km,
            forecast_horizon_minutes=request.forecast_horizon_minutes,
            time_interval_minutes=2
        )
        
        # Calculate current ETA (if leaving now)
        from app.services.trafficcams.domain.departure_time_optimizer import ETACalculationStrategy
        eta_calc = ETACalculationStrategy()
        current_eta = eta_calc.calculate_eta_from_ci(
            request.original_eta_minutes,
            result.current_average_ci
        )
        
        # Generate recommendation text
        recommendation_text = _generate_recommendation_text(result, current_eta)
        
        # Convert to response DTO
        response = OptimalDepartureResponse(
            best_time_minutes_from_now=result.best_time_minutes_from_now,
            best_departure_time=result.best_departure_time.isoformat(),
            original_eta_minutes=result.original_eta_minutes,
            current_eta_minutes=current_eta,
            optimized_eta_minutes=result.optimized_eta_minutes,
            time_saved_minutes=result.time_saved_minutes,
            current_average_ci=result.current_average_ci,
            optimal_average_ci=result.optimal_average_ci,
            cameras_analyzed=result.cameras_analyzed,
            confidence_score=result.confidence_score,
            recommendation_text=recommendation_text
        )
        
        logger.info(f"Optimization complete: {recommendation_text}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error optimizing departure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize departure time: {str(e)}"
        )


def _generate_recommendation_text(result, current_eta: int) -> str:
    """
    Generate human-readable recommendation text
    
    Design Pattern: Template Method Pattern
    """
    if result.cameras_analyzed == 0:
        return "No traffic data available for this route"
    
    if result.best_time_minutes_from_now == 0:
        return f"Leave now! Current ETA: {current_eta} minutes"
    
    if result.time_saved_minutes > 5:
        return (
            f"Wait {result.best_time_minutes_from_now} minutes for better traffic. "
            f"You'll save {result.time_saved_minutes} minutes! "
            f"ETA: {result.optimized_eta_minutes} min"
        )
    elif result.time_saved_minutes > 0:
        return (
            f"Waiting {result.best_time_minutes_from_now} minutes may save "
            f"{result.time_saved_minutes} minutes. ETA: {result.optimized_eta_minutes} min"
        )
    else:
        return (
            f"Traffic is similar now and later. "
            f"Current ETA: {current_eta} min"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Departure Time Optimization API",
        "timestamp": datetime.now().isoformat()
    }
