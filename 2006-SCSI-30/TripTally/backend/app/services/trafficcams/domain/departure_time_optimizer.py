"""
Departure Time Optimizer Service
Finds the best time to leave based on traffic congestion forecasts

Design Pattern: Strategy Pattern for CI-to-ETA calculations
Architecture: Domain-Driven Design with clear separation of concerns
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dataclasses import dataclass
import math

from .route_models import Point, LineString, RouteCameraInfo
from .geospatial_service import GeospatialService
from .camera_loader import CameraDataLoader
from ..data_repository import DataRepository
from ..models import Camera, CIForecast
from ..logger import get_logger
import re

logger = get_logger("departure_optimizer")


@dataclass
class CameraCI:
    """Camera with its CI value"""
    camera_id: str
    latitude: float
    longitude: float
    ci: float
    distance_to_route: float


@dataclass
class TimeSlotAnalysis:
    """Analysis for a specific time slot"""
    minutes_from_now: int
    timestamp: datetime
    total_ci: float
    average_ci: float
    camera_count: int
    cameras: List[CameraCI]


@dataclass
class OptimalDepartureResult:
    """Result of optimal departure time analysis"""
    best_time_minutes_from_now: int
    best_departure_time: datetime
    original_eta_minutes: int
    optimized_eta_minutes: int
    time_saved_minutes: int
    current_total_ci: float
    optimal_total_ci: float
    current_average_ci: float
    optimal_average_ci: float
    cameras_analyzed: int
    confidence_score: float  # 0.0 to 1.0


class ETACalculationStrategy:
    """
    Strategy Pattern: Different strategies for calculating ETA based on CI
    This allows easy extension with different algorithms
    """
    
    BASE_SPEED_KMH = 60.0  # Free-flow speed
    
    @staticmethod
    def calculate_eta_from_ci(base_eta_minutes: int, average_ci: float) -> int:
        """
        Calculate adjusted ETA based on average CI
        
        Simple model:
        - CI 0.0-0.2: Free flow, no impact (100% speed)
        - CI 0.2-0.4: Light traffic, 10% slower
        - CI 0.4-0.6: Moderate traffic, 25% slower
        - CI 0.6-0.8: Heavy traffic, 50% slower
        - CI 0.8-1.0: Severe congestion, 100% slower
        
        Args:
            base_eta_minutes: Original ETA in free-flow conditions
            average_ci: Average congestion index (0.0 to 1.0)
            
        Returns:
            Adjusted ETA in minutes
        """
        if average_ci < 0.2:
            # Free flow
            multiplier = 1.0
        elif average_ci < 0.4:
            # Light traffic
            multiplier = 1.1
        elif average_ci < 0.6:
            # Moderate traffic
            multiplier = 1.25
        elif average_ci < 0.8:
            # Heavy traffic
            multiplier = 1.5
        else:
            # Severe congestion
            multiplier = 2.0
        
        adjusted_eta = int(base_eta_minutes * multiplier)
        return max(adjusted_eta, base_eta_minutes)  # Never faster than base


class DepartureTimeOptimizer:
    """
    Service for finding optimal departure time
    
    Design Pattern: Facade Pattern - provides simple interface to complex subsystem
    """
    
    def __init__(
        self,
        repository: DataRepository,
        geospatial_service: GeospatialService,
        camera_loader: CameraDataLoader,
        eta_strategy: ETACalculationStrategy = None
    ):
        """
        Initialize optimizer
        
        Args:
            repository: Data repository for CI values and forecasts
            geospatial_service: Service for geographic calculations
            camera_loader: Loader for camera metadata
            eta_strategy: Strategy for ETA calculation (optional, uses default if None)
        """
        self.repository = repository
        self.geospatial = geospatial_service
        self.camera_loader = camera_loader
        self.eta_strategy = eta_strategy or ETACalculationStrategy()
        
    def find_optimal_departure(
        self,
        route_points: List[Point],
        original_eta_minutes: int,
        search_radius_km: float = 0.5,
        forecast_horizon_minutes: int = 120,
        time_interval_minutes: int = 2
    ) -> OptimalDepartureResult:
        """
        Find the optimal departure time based on traffic forecasts
        
        Algorithm:
        1. Convert route points to LineString
        2. Find cameras within radius of route
        3. Get current CI for all cameras
        4. For each time slot in forecast horizon:
           - Get forecasted CI for all cameras
           - Calculate total and average CI
        5. Find time slot with minimum CI
        6. Calculate optimized ETA
        7. Return recommendation
        
        Args:
            route_points: List of points defining the route
            original_eta_minutes: Original travel time estimate
            search_radius_km: Radius to search for cameras (default: 0.5km)
            forecast_horizon_minutes: How far ahead to look (default: 120 min)
            time_interval_minutes: Time slot granularity (default: 2 min)
            
        Returns:
            OptimalDepartureResult with best time and updated ETA
        """
        logger.info(f"Finding optimal departure for route with {len(route_points)} points")
        
        # Step 1: Create LineString from route
        route = LineString(points=route_points)
        
        # Step 2: Find cameras near route
        cameras_near_route = self._find_cameras_near_route(route, search_radius_km)
        
        if not cameras_near_route:
            logger.warning("No cameras found near route, returning original ETA")
            return self._create_no_optimization_result(original_eta_minutes)
        
        logger.info(f"Found {len(cameras_near_route)} cameras within {search_radius_km}km of route")
        
        # Step 3: Analyze current conditions
        current_analysis = self._analyze_current_conditions(cameras_near_route)
        
        # Step 4: Analyze forecast time slots
        time_slots = self._generate_time_slots(forecast_horizon_minutes, time_interval_minutes)
        forecast_analyses = self._analyze_forecast_time_slots(
            cameras_near_route,
            time_slots
        )
        
        # Step 5: Find optimal time slot (minimum CI)
        optimal_analysis = min(forecast_analyses, key=lambda x: x.average_ci)
        
        # Step 6: Calculate ETAs
        current_eta = self.eta_strategy.calculate_eta_from_ci(
            original_eta_minutes,
            current_analysis.average_ci
        )
        
        optimal_eta = self.eta_strategy.calculate_eta_from_ci(
            original_eta_minutes,
            optimal_analysis.average_ci
        )
        
        time_saved = current_eta - optimal_eta
        
        # Step 7: Calculate confidence score
        confidence = self._calculate_confidence(
            current_analysis,
            optimal_analysis,
            len(cameras_near_route)
        )
        
        result = OptimalDepartureResult(
            best_time_minutes_from_now=optimal_analysis.minutes_from_now,
            best_departure_time=optimal_analysis.timestamp,
            original_eta_minutes=original_eta_minutes,
            optimized_eta_minutes=optimal_eta,
            time_saved_minutes=time_saved,
            current_total_ci=current_analysis.total_ci,
            optimal_total_ci=optimal_analysis.total_ci,
            current_average_ci=current_analysis.average_ci,
            optimal_average_ci=optimal_analysis.average_ci,
            cameras_analyzed=len(cameras_near_route),
            confidence_score=confidence
        )
        
        logger.info(
            f"Optimal departure: +{result.best_time_minutes_from_now} min, "
            f"ETA: {result.optimized_eta_minutes} min (saves {time_saved} min)"
        )
        
        return result
    
    def _find_cameras_near_route(
        self,
        route: LineString,
        radius_km: float
    ) -> List[RouteCameraInfo]:
        """
        Find cameras within radius of route
        
        Returns:
            List of RouteCameraInfo objects
        """
        all_cameras = self.camera_loader.load_cameras()
        cameras_near_route = self.geospatial.find_cameras_along_route(
            route,
            all_cameras,
            search_radius_km=radius_km
        )
        return cameras_near_route
    
    def _analyze_current_conditions(
        self,
        cameras_near_route: List[RouteCameraInfo]
    ) -> TimeSlotAnalysis:
        """Analyze current traffic conditions"""
        now = datetime.now()
        camera_cis = []
        total_ci = 0.0
        
        for camera_info in cameras_near_route:
            ci_state = self.repository.get_ci_state(camera_info.camera_id)
            # Handle both dict (from Redis) and CIState object
            if ci_state:
                if isinstance(ci_state, dict):
                    if 'CI' in ci_state and ci_state['CI'] is not None:
                        ci = float(ci_state['CI'])
                    elif 'ci' in ci_state and ci_state['ci'] is not None:
                        ci = float(ci_state['ci'])
                    else:
                        ci = 0.3
                else:
                    ci = ci_state.ci
            else:
                ci = 0.3  # Default to light traffic
            
            camera_cis.append(CameraCI(
                camera_id=camera_info.camera_id,
                latitude=camera_info.latitude,
                longitude=camera_info.longitude,
                ci=ci,
                distance_to_route=camera_info.distance_to_route
            ))
            total_ci += ci
        
        avg_ci = total_ci / len(cameras_near_route) if cameras_near_route else 0.0
        
        return TimeSlotAnalysis(
            minutes_from_now=0,
            timestamp=now,
            total_ci=total_ci,
            average_ci=avg_ci,
            camera_count=len(cameras_near_route),
            cameras=camera_cis
        )
    
    def _generate_time_slots(
        self,
        horizon_minutes: int,
        interval_minutes: int
    ) -> List[Tuple[int, datetime]]:
        """
        Generate time slots for analysis
        
        Returns:
            List of (minutes_from_now, timestamp) tuples
        """
        now = datetime.now()
        slots = []
        
        for minutes in range(0, horizon_minutes + 1, interval_minutes):
            timestamp = now + timedelta(minutes=minutes)
            slots.append((minutes, timestamp))
        
        return slots
    
    def _analyze_forecast_time_slots(
        self,
        cameras_near_route: List[RouteCameraInfo],
        time_slots: List[Tuple[int, datetime]]
    ) -> List[TimeSlotAnalysis]:
        """
        Analyze each forecast time slot
        
        Returns:
            List of TimeSlotAnalysis for each time slot
        """
        analyses = []
        
        for minutes_from_now, timestamp in time_slots:
            camera_cis = []
            total_ci = 0.0
            
            for camera_info in cameras_near_route:
                # Get forecasted CI for this camera at this time
                forecast = self.repository.get_forecast(camera_info.camera_id)
                
                # Find the forecast horizon closest to our target time
                ci = 0.3  # Default to light traffic
                if forecast:
                    # Handle both dict (from Redis) and CIForecast object
                    if isinstance(forecast, dict):
                        # Parse horizons from Redis dict format
                        # The forecast dict has keys like "h_2", "h_4", etc. with CI values
                        best_match_key = None
                        best_match_diff = float('inf')
                        
                        for key in forecast.keys():
                            m = re.match(r'^h[:_]?(\d+)$', str(key))
                            if not m: 
                                continue
                            try:
                                horizon_min = int(m.group(1))
                                diff = abs(horizon_min - minutes_from_now)
                                if diff < best_match_diff:
                                    best_match_diff = diff
                                    best_match_key = key
                            except (ValueError, IndexError):
                                continue
                        
                        if best_match_key:
                            ci = float(forecast[best_match_key])
                    elif hasattr(forecast, 'horizons') and forecast.horizons:
                        # CIForecast object
                        closest_horizon = min(
                            forecast.horizons,
                            key=lambda h: abs(h.horizon_minutes - minutes_from_now)
                        )
                        ci = closest_horizon.predicted_ci
                
                camera_cis.append(CameraCI(
                    camera_id=camera_info.camera_id,
                    latitude=camera_info.latitude,
                    longitude=camera_info.longitude,
                    ci=ci,
                    distance_to_route=camera_info.distance_to_route
                ))
                total_ci += ci
            
            avg_ci = total_ci / len(cameras_near_route) if cameras_near_route else 0.0
            
            analyses.append(TimeSlotAnalysis(
                minutes_from_now=minutes_from_now,
                timestamp=timestamp,
                total_ci=total_ci,
                average_ci=avg_ci,
                camera_count=len(cameras_near_route),
                cameras=camera_cis
            ))

        logger.info("minimum timeslot and ci")
        optimal_analysis = min(analyses, key=lambda x: x.average_ci)
        logger.info(f"Optimal slot: {optimal_analysis.minutes_from_now} min, avg CI: {optimal_analysis.average_ci:.3f}")
        return analyses
    
    def _calculate_confidence(
        self,
        current: TimeSlotAnalysis,
        optimal: TimeSlotAnalysis,
        camera_count: int
    ) -> float:
        """
        Calculate confidence score for the recommendation
        
        Factors:
        - Number of cameras (more = higher confidence)
        - CI difference (bigger difference = higher confidence)
        - Time window (nearer future = higher confidence)
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Camera count factor (more cameras = higher confidence)
        camera_factor = min(camera_count / 10.0, 1.0)  # Max out at 10 cameras
        
        # CI difference factor
        ci_diff = abs(current.average_ci - optimal.average_ci)
        ci_factor = min(ci_diff * 2.0, 1.0)  # Normalize to 0-1
        
        # Time factor (prefer nearer predictions)
        time_factor = max(0.5, 1.0 - (optimal.minutes_from_now / 120.0) * 0.5)
        
        # Weighted average
        confidence = (camera_factor * 0.4 + ci_factor * 0.4 + time_factor * 0.2)
        
        return round(confidence, 2)
    
    def _create_no_optimization_result(
        self,
        original_eta_minutes: int
    ) -> OptimalDepartureResult:
        """Create result when no optimization is possible"""
        now = datetime.now()
        
        return OptimalDepartureResult(
            best_time_minutes_from_now=0,
            best_departure_time=now,
            original_eta_minutes=original_eta_minutes,
            optimized_eta_minutes=original_eta_minutes,
            time_saved_minutes=0,
            current_total_ci=0.0,
            optimal_total_ci=0.0,
            current_average_ci=0.0,
            optimal_average_ci=0.0,
            cameras_analyzed=0,
            confidence_score=0.0
        )
