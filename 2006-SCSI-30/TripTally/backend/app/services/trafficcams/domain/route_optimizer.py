"""
Route Optimization Service
Core business logic for finding optimal departure times
"""

from datetime import datetime, timedelta
from typing import List, Optional
import math

from .route_models import (
    LineString, RouteCameraInfo, DepartureOption, 
    RouteOptimizationResult, CameraTrafficInfo
)
from .geospatial_service import GeospatialService
from .camera_loader import CameraDataLoader
from ..data_repository import DataRepository
from ..models import Camera, CIForecast, ForecastHorizon
from ..logger import get_logger

logger = get_logger("route_optimizer")


class RouteOptimizationService:
    """Service for route-based traffic optimization"""
    
    # Constants for travel time estimation
    BASE_SPEED_KMH = 60.0  # Base speed in free-flow conditions
    CI_SPEED_FACTORS = {
        # CI range -> speed multiplier
        0.0: 1.0,   # Free flow: 100% speed
        0.3: 0.9,   # Light: 90% speed
        0.5: 0.7,   # Moderate: 70% speed
        0.7: 0.5,   # Heavy: 50% speed
        0.9: 0.3,   # Severe: 30% speed
    }
    
    def __init__(
        self,
        repository: DataRepository,
        geospatial_service: GeospatialService,
        camera_loader: CameraDataLoader
    ):
        """
        Initialize optimization service
        
        Args:
            repository: Data repository for accessing camera data and forecasts
            geospatial_service: Service for geographic calculations
            camera_loader: Loader for camera metadata from JSON file
        """
        self.repository = repository
        self.geo_service = geospatial_service
        self.camera_loader = camera_loader
    
    def _get_speed_factor(self, ci: float) -> float:
        """
        Calculate speed factor based on CI
        
        Args:
            ci: Congestion Index (0.0 to 1.0)
            
        Returns:
            Speed multiplier (0.0 to 1.0)
        """
        ci = max(0.0, min(1.0, ci))
        
        # Find the two CI thresholds that bracket this CI
        thresholds = sorted(self.CI_SPEED_FACTORS.keys())
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= ci < thresholds[i + 1]:
                # Linear interpolation
                ci_low = thresholds[i]
                ci_high = thresholds[i + 1]
                factor_low = self.CI_SPEED_FACTORS[ci_low]
                factor_high = self.CI_SPEED_FACTORS[ci_high]
                
                t = (ci - ci_low) / (ci_high - ci_low)
                return factor_low + t * (factor_high - factor_low)
        
        # Handle edge cases
        if ci >= thresholds[-1]:
            return self.CI_SPEED_FACTORS[thresholds[-1]]
        return self.CI_SPEED_FACTORS[thresholds[0]]
    
    def _estimate_travel_time(
        self,
        route_length_km: float,
        average_ci: float
    ) -> float:
        """
        Estimate travel time based on route length and traffic
        
        Args:
            route_length_km: Route length in kilometers
            average_ci: Average congestion index along route
            
        Returns:
            Estimated travel time in minutes
        """
        speed_factor = self._get_speed_factor(average_ci)
        effective_speed = self.BASE_SPEED_KMH * speed_factor
        
        # Avoid division by zero
        if effective_speed <= 0:
            effective_speed = self.BASE_SPEED_KMH * 0.1
        
        travel_hours = route_length_km / effective_speed
        return travel_hours * 60  # Convert to minutes
    
    def _get_forecast_at_horizon(
        self,
        forecast: Optional[CIForecast],
        horizon_minutes: int
    ) -> Optional[float]:
        """
        Get forecast CI at specific horizon
        
        Args:
            forecast: CI forecast
            horizon_minutes: Minutes into future
            
        Returns:
            Predicted CI or None if not available
        """
        if not forecast or not forecast.horizons:
            return None
        
        # Find closest horizon
        closest_horizon = min(
            forecast.horizons,
            key=lambda h: abs(h.horizon_minutes - horizon_minutes)
        )
        
        # Only use if within reasonable range (±10 minutes)
        if abs(closest_horizon.horizon_minutes - horizon_minutes) <= 10:
            return closest_horizon.predicted_ci
        
        return None
    
    def _calculate_confidence(
        self,
        camera_forecasts: List[CameraTrafficInfo],
        horizon_minutes: int
    ) -> float:
        """
        Calculate confidence score for departure option
        
        Args:
            camera_forecasts: List of camera traffic info
            horizon_minutes: Forecast horizon
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not camera_forecasts:
            return 0.0
        
        # Factors affecting confidence:
        # 1. Number of cameras (more = better)
        # 2. Forecast horizon (closer = better)
        # 3. Data availability (complete = better)
        
        camera_factor = min(1.0, len(camera_forecasts) / 5.0)  # Max out at 5 cameras
        
        # Horizon factor: decreases linearly from 1.0 at 0 min to 0.5 at 120 min
        horizon_factor = max(0.5, 1.0 - (horizon_minutes / 240.0))
        
        # Data availability: percentage with valid forecasts
        valid_forecasts = sum(1 for c in camera_forecasts if c.forecast_ci > 0)
        availability_factor = valid_forecasts / len(camera_forecasts) if camera_forecasts else 0
        
        # Combine factors
        confidence = (camera_factor * 0.3 + 
                     horizon_factor * 0.4 + 
                     availability_factor * 0.3)
        
        return round(confidence, 2)
    
    def optimize_route(
        self,
        route: LineString,
        original_eta_minutes: int,
        search_radius_km: float = 0.5,
        forecast_horizon_minutes: int = 120
    ) -> RouteOptimizationResult:
        """
        Find optimal departure time for a route
        
        Args:
            route: Route as LineString
            original_eta_minutes: Original estimated travel time
            search_radius_km: Search radius for cameras (default: 500m)
            forecast_horizon_minutes: How far ahead to analyze (default: 120 min)
            
        Returns:
            RouteOptimizationResult with best departure time and alternatives
        """
        logger.info(f"Starting route optimization for {len(route.points)} point route")
        
        # 1. Load all cameras from JSON file
        all_cameras = self.camera_loader.load_cameras()
        logger.info(f"Loaded {len(all_cameras)} cameras from static data")
        
        # 2. Find cameras along route (filters to only cameras within search radius)
        route_cameras = self.geo_service.find_cameras_along_route(
            route, all_cameras, search_radius_km
        )
        
        logger.info(f"Found {len(route_cameras)} cameras along route")
        
        if not route_cameras:
            logger.warning("No cameras found along route")
            # Return result with no optimization possible
            now = datetime.now()
            return RouteOptimizationResult(
                original_eta=now + timedelta(minutes=original_eta_minutes),
                original_departure=now,
                route_cameras=[],
                best_departure=DepartureOption(
                    departure_time=now,
                    minutes_from_now=0,
                    average_ci=0.5,
                    max_ci=0.5,
                    estimated_travel_time_minutes=original_eta_minutes,
                    new_eta=now + timedelta(minutes=original_eta_minutes),
                    confidence_score=0.0,
                    camera_forecasts=[]
                )
            )
        
        # 3. Calculate route length for travel time estimation
        route_length_km = self.geo_service.calculate_route_length(route)
        logger.info(f"Route length: {route_length_km:.2f} km")
        
        # 4. Analyze departure options (every 10 minutes for next 2 hours)
        now = datetime.now()
        departure_options = []
        
        for minutes_ahead in range(0, forecast_horizon_minutes + 1, 10):
            departure_time = now + timedelta(minutes=minutes_ahead)
            camera_forecasts = []
            
            # Get forecasts for all route cameras at this departure time
            for route_cam in route_cameras:
                forecast = self.repository.get_forecast(route_cam.camera_id)
                ci_state = self.repository.get_ci_state(route_cam.camera_id)
                
                # Determine CI at departure time
                if minutes_ahead == 0:
                    # Current time - use current CI
                    forecast_ci = ci_state.ci if ci_state else 0.5
                else:
                    # Future time - use forecast
                    forecast_ci = self._get_forecast_at_horizon(forecast, minutes_ahead)
                    if forecast_ci is None:
                        forecast_ci = ci_state.ci if ci_state else 0.5
                
                camera_forecasts.append(CameraTrafficInfo(
                    camera_id=route_cam.camera_id,
                    current_ci=ci_state.ci if ci_state else 0.5,
                    forecast_ci=forecast_ci,
                    timestamp=departure_time
                ))
            
            # Calculate statistics
            if camera_forecasts:
                forecast_cis = [c.forecast_ci for c in camera_forecasts]
                average_ci = sum(forecast_cis) / len(forecast_cis)
                max_ci = max(forecast_cis)
            else:
                average_ci = 0.5
                max_ci = 0.5
            
            # Estimate travel time based on traffic
            travel_time = self._estimate_travel_time(route_length_km, average_ci)
            new_eta = departure_time + timedelta(minutes=travel_time)
            
            # Calculate confidence
            confidence = self._calculate_confidence(camera_forecasts, minutes_ahead)
            
            departure_option = DepartureOption(
                departure_time=departure_time,
                minutes_from_now=minutes_ahead,
                average_ci=round(average_ci, 3),
                max_ci=round(max_ci, 3),
                estimated_travel_time_minutes=round(travel_time, 1),
                new_eta=new_eta,
                confidence_score=confidence,
                camera_forecasts=camera_forecasts
            )
            
            departure_options.append(departure_option)
        
        # 5. Find best departure time
        # Best = lowest average CI, or if similar, earliest departure
        best_option = min(
            departure_options,
            key=lambda opt: (opt.average_ci, opt.minutes_from_now)
        )
        
        # 6. Identify alternatives (next 3 best options)
        sorted_options = sorted(
            departure_options,
            key=lambda opt: (opt.average_ci, opt.minutes_from_now)
        )
        alternatives = [opt for opt in sorted_options[1:4] if opt != best_option]
        
        logger.info(f"Best departure: {best_option.minutes_from_now} min from now, "
                   f"avg CI={best_option.average_ci:.3f}")
        
        return RouteOptimizationResult(
            original_eta=now + timedelta(minutes=original_eta_minutes),
            original_departure=now,
            route_cameras=route_cameras,
            best_departure=best_option,
            alternative_departures=alternatives
        )
