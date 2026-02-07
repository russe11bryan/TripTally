"""
Unit tests for Departure Time Optimizer Service
Coverage: 100% of domain/departure_time_optimizer.py

Testing Strategy:
- Unit tests with mocked dependencies
- Test all methods and code paths
- Test edge cases and error conditions
- Test design patterns (Strategy, Facade)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/services/trafficcams'))

from domain.departure_time_optimizer import (
    DepartureTimeOptimizer,
    ETACalculationStrategy,
    CameraCI,
    TimeSlotAnalysis,
    OptimalDepartureResult
)
from domain.route_models import Point, LineString
from models import Camera, CIForecast


class TestETACalculationStrategy:
    """Test ETA calculation strategy (Strategy Pattern)"""
    
    def test_calculate_eta_free_flow(self):
        """Test ETA calculation with free-flow traffic (CI < 0.2)"""
        strategy = ETACalculationStrategy()
        
        # CI = 0.1 (free flow) should not increase ETA
        eta = strategy.calculate_eta_from_ci(30, 0.1)
        assert eta == 30
        
        # CI = 0.0 (no traffic) should not increase ETA
        eta = strategy.calculate_eta_from_ci(45, 0.0)
        assert eta == 45
    
    def test_calculate_eta_light_traffic(self):
        """Test ETA calculation with light traffic (0.2 <= CI < 0.4)"""
        strategy = ETACalculationStrategy()
        
        # CI = 0.25 (light) should increase by 10%
        eta = strategy.calculate_eta_from_ci(30, 0.25)
        assert eta == 33  # 30 * 1.1 = 33
        
        # CI = 0.35 (light) should increase by 10%
        eta = strategy.calculate_eta_from_ci(60, 0.35)
        assert eta == 66  # 60 * 1.1 = 66
    
    def test_calculate_eta_moderate_traffic(self):
        """Test ETA calculation with moderate traffic (0.4 <= CI < 0.6)"""
        strategy = ETACalculationStrategy()
        
        # CI = 0.45 (moderate) should increase by 25%
        eta = strategy.calculate_eta_from_ci(40, 0.45)
        assert eta == 50  # 40 * 1.25 = 50
        
        # CI = 0.55 (moderate) should increase by 25%
        eta = strategy.calculate_eta_from_ci(20, 0.55)
        assert eta == 25  # 20 * 1.25 = 25
    
    def test_calculate_eta_heavy_traffic(self):
        """Test ETA calculation with heavy traffic (0.6 <= CI < 0.8)"""
        strategy = ETACalculationStrategy()
        
        # CI = 0.65 (heavy) should increase by 50%
        eta = strategy.calculate_eta_from_ci(30, 0.65)
        assert eta == 45  # 30 * 1.5 = 45
        
        # CI = 0.75 (heavy) should increase by 50%
        eta = strategy.calculate_eta_from_ci(50, 0.75)
        assert eta == 75  # 50 * 1.5 = 75
    
    def test_calculate_eta_severe_congestion(self):
        """Test ETA calculation with severe congestion (CI >= 0.8)"""
        strategy = ETACalculationStrategy()
        
        # CI = 0.85 (severe) should double ETA
        eta = strategy.calculate_eta_from_ci(25, 0.85)
        assert eta == 50  # 25 * 2.0 = 50
        
        # CI = 1.0 (maximum) should double ETA
        eta = strategy.calculate_eta_from_ci(60, 1.0)
        assert eta == 120  # 60 * 2.0 = 120
    
    def test_calculate_eta_never_faster_than_base(self):
        """Test that ETA is never faster than base ETA"""
        strategy = ETACalculationStrategy()
        
        # Even with CI = 0, should not be faster
        eta = strategy.calculate_eta_from_ci(30, 0.0)
        assert eta >= 30
        
        # Even with negative CI (invalid), should not be faster
        eta = strategy.calculate_eta_from_ci(40, -0.1)
        assert eta >= 40


class TestCameraCI:
    """Test CameraCI dataclass"""
    
    def test_camera_ci_creation(self):
        """Test creating CameraCI object"""
        camera_ci = CameraCI(
            camera_id="1001",
            latitude=1.3521,
            longitude=103.8198,
            ci=0.45,
            distance_to_route=0.3
        )
        
        assert camera_ci.camera_id == "1001"
        assert camera_ci.latitude == 1.3521
        assert camera_ci.longitude == 103.8198
        assert camera_ci.ci == 0.45
        assert camera_ci.distance_to_route == 0.3


class TestTimeSlotAnalysis:
    """Test TimeSlotAnalysis dataclass"""
    
    def test_time_slot_analysis_creation(self):
        """Test creating TimeSlotAnalysis object"""
        now = datetime.now()
        cameras = [
            CameraCI("1001", 1.35, 103.82, 0.4, 0.2),
            CameraCI("1002", 1.36, 103.83, 0.5, 0.3),
        ]
        
        analysis = TimeSlotAnalysis(
            minutes_from_now=15,
            timestamp=now + timedelta(minutes=15),
            total_ci=0.9,
            average_ci=0.45,
            camera_count=2,
            cameras=cameras
        )
        
        assert analysis.minutes_from_now == 15
        assert analysis.total_ci == 0.9
        assert analysis.average_ci == 0.45
        assert analysis.camera_count == 2
        assert len(analysis.cameras) == 2


class TestOptimalDepartureResult:
    """Test OptimalDepartureResult dataclass"""
    
    def test_optimal_departure_result_creation(self):
        """Test creating OptimalDepartureResult object"""
        now = datetime.now()
        
        result = OptimalDepartureResult(
            best_time_minutes_from_now=15,
            best_departure_time=now + timedelta(minutes=15),
            original_eta_minutes=30,
            optimized_eta_minutes=25,
            time_saved_minutes=5,
            current_total_ci=1.5,
            optimal_total_ci=1.0,
            current_average_ci=0.5,
            optimal_average_ci=0.33,
            cameras_analyzed=3,
            confidence_score=0.75
        )
        
        assert result.best_time_minutes_from_now == 15
        assert result.original_eta_minutes == 30
        assert result.optimized_eta_minutes == 25
        assert result.time_saved_minutes == 5
        assert result.confidence_score == 0.75


class TestDepartureTimeOptimizer:
    """Test DepartureTimeOptimizer service (Facade Pattern)"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing"""
        mock_repo = Mock()
        mock_geospatial = Mock()
        mock_camera_loader = Mock()
        mock_eta_strategy = Mock(spec=ETACalculationStrategy)
        
        return {
            'repository': mock_repo,
            'geospatial_service': mock_geospatial,
            'camera_loader': mock_camera_loader,
            'eta_strategy': mock_eta_strategy
        }
    
    def test_optimizer_initialization(self, mock_dependencies):
        """Test optimizer initialization"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        assert optimizer.repository == mock_dependencies['repository']
        assert optimizer.geospatial == mock_dependencies['geospatial_service']
        assert optimizer.camera_loader == mock_dependencies['camera_loader']
        assert optimizer.eta_strategy == mock_dependencies['eta_strategy']
    
    def test_optimizer_initialization_with_default_strategy(self, mock_dependencies):
        """Test optimizer initialization with default ETA strategy"""
        del mock_dependencies['eta_strategy']
        
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        assert isinstance(optimizer.eta_strategy, ETACalculationStrategy)
    
    def test_find_cameras_near_route(self, mock_dependencies):
        """Test finding cameras near route"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock cameras
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        camera2 = Camera(camera_id="1002", latitude=1.36, longitude=103.83)
        mock_dependencies['camera_loader'].load_cameras.return_value = [camera1, camera2]
        
        # Mock geospatial service
        mock_dependencies['geospatial_service'].find_cameras_along_route.return_value = [
            (camera1, 0.2),
            (camera2, 0.4)
        ]
        
        # Create route
        route = LineString(points=[
            Point(latitude=1.35, longitude=103.82),
            Point(latitude=1.36, longitude=103.83)
        ])
        
        # Find cameras
        cameras = optimizer._find_cameras_near_route(route, 0.5)
        
        assert len(cameras) == 2
        assert cameras[0][0].camera_id == "1001"
        assert cameras[0][1] == 0.2
        assert cameras[1][0].camera_id == "1002"
        assert cameras[1][1] == 0.4
    
    def test_analyze_current_conditions(self, mock_dependencies):
        """Test analyzing current traffic conditions"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock cameras
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        camera2 = Camera(camera_id="1002", latitude=1.36, longitude=103.83)
        cameras_near_route = [(camera1, 0.2), (camera2, 0.4)]
        
        # Mock repository
        mock_dependencies['repository'].get_latest_ci.side_effect = [0.4, 0.6]
        
        # Analyze
        analysis = optimizer._analyze_current_conditions(cameras_near_route)
        
        assert analysis.minutes_from_now == 0
        assert analysis.camera_count == 2
        assert analysis.total_ci == 1.0  # 0.4 + 0.6
        assert analysis.average_ci == 0.5  # 1.0 / 2
        assert len(analysis.cameras) == 2
        assert analysis.cameras[0].ci == 0.4
        assert analysis.cameras[1].ci == 0.6
    
    def test_analyze_current_conditions_with_missing_data(self, mock_dependencies):
        """Test analyzing current conditions when CI data is missing"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock camera
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        cameras_near_route = [(camera1, 0.2)]
        
        # Mock repository returning None (missing data)
        mock_dependencies['repository'].get_latest_ci.return_value = None
        
        # Analyze
        analysis = optimizer._analyze_current_conditions(cameras_near_route)
        
        # Should use default value 0.3
        assert analysis.cameras[0].ci == 0.3
        assert analysis.total_ci == 0.3
        assert analysis.average_ci == 0.3
    
    def test_generate_time_slots(self, mock_dependencies):
        """Test generating time slots"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Generate slots: 0, 2, 4, ..., 120 minutes
        slots = optimizer._generate_time_slots(120, 2)
        
        assert len(slots) == 61  # 0 to 120 inclusive, step 2
        assert slots[0][0] == 0  # First slot at 0 minutes
        assert slots[-1][0] == 120  # Last slot at 120 minutes
        assert slots[1][0] == 2  # Second slot at 2 minutes
        
        # Check timestamps
        now = datetime.now()
        for minutes, timestamp in slots:
            # Timestamp should be approximately now + minutes
            expected = now + timedelta(minutes=minutes)
            diff = abs((timestamp - expected).total_seconds())
            assert diff < 1  # Within 1 second
    
    def test_analyze_forecast_time_slots(self, mock_dependencies):
        """Test analyzing forecast time slots"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock cameras
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        camera2 = Camera(camera_id="1002", latitude=1.36, longitude=103.83)
        cameras_near_route = [(camera1, 0.2), (camera2, 0.4)]
        
        # Mock forecasts - create simple mock objects with ci attribute
        mock_forecast1 = Mock()
        mock_forecast1.ci = 0.3
        mock_forecast2 = Mock()
        mock_forecast2.ci = 0.4
        mock_forecast3 = Mock()
        mock_forecast3.ci = 0.2
        mock_forecast4 = Mock()
        mock_forecast4.ci = 0.3
        
        mock_dependencies['repository'].get_forecast.side_effect = [
            mock_forecast1,
            mock_forecast2,
            mock_forecast3,
            mock_forecast4,
        ]
        
        # Generate time slots
        now = datetime.now()
        time_slots = [
            (0, now),
            (10, now + timedelta(minutes=10))
        ]
        
        # Analyze
        analyses = optimizer._analyze_forecast_time_slots(cameras_near_route, time_slots)
        
        assert len(analyses) == 2
        
        # First slot (0 minutes)
        assert analyses[0].minutes_from_now == 0
        assert analyses[0].total_ci == 0.7  # 0.3 + 0.4
        assert analyses[0].average_ci == 0.35
        
        # Second slot (10 minutes)
        assert analyses[1].minutes_from_now == 10
        assert analyses[1].total_ci == 0.5  # 0.2 + 0.3
        assert analyses[1].average_ci == 0.25
    
    def test_analyze_forecast_with_missing_forecasts(self, mock_dependencies):
        """Test analyzing forecasts when some are missing"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock camera
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        cameras_near_route = [(camera1, 0.2)]
        
        # Mock repository returning None (missing forecast)
        mock_dependencies['repository'].get_forecast.return_value = None
        
        # Time slot
        now = datetime.now()
        time_slots = [(0, now)]
        
        # Analyze
        analyses = optimizer._analyze_forecast_time_slots(cameras_near_route, time_slots)
        
        # Should use default value 0.3
        assert analyses[0].cameras[0].ci == 0.3
        assert analyses[0].total_ci == 0.3
        assert analyses[0].average_ci == 0.3
    
    def test_calculate_confidence_high(self, mock_dependencies):
        """Test confidence calculation with high confidence"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # High confidence: many cameras, big CI difference, near time
        current = TimeSlotAnalysis(
            minutes_from_now=0,
            timestamp=datetime.now(),
            total_ci=2.0,
            average_ci=0.5,
            camera_count=10,
            cameras=[]
        )
        
        optimal = TimeSlotAnalysis(
            minutes_from_now=5,  # Near future
            timestamp=datetime.now() + timedelta(minutes=5),
            total_ci=1.0,
            average_ci=0.25,  # Much lower CI
            camera_count=10,
            cameras=[]
        )
        
        confidence = optimizer._calculate_confidence(current, optimal, 10)
        
        # Should be high confidence (many cameras, big difference, near time)
        assert confidence > 0.7
        assert confidence <= 1.0
    
    def test_calculate_confidence_low(self, mock_dependencies):
        """Test confidence calculation with low confidence"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Low confidence: few cameras, small CI difference, far time
        current = TimeSlotAnalysis(
            minutes_from_now=0,
            timestamp=datetime.now(),
            total_ci=0.6,
            average_ci=0.3,
            camera_count=2,
            cameras=[]
        )
        
        optimal = TimeSlotAnalysis(
            minutes_from_now=120,  # Far future
            timestamp=datetime.now() + timedelta(minutes=120),
            total_ci=0.5,
            average_ci=0.25,  # Small difference
            camera_count=2,
            cameras=[]
        )
        
        confidence = optimizer._calculate_confidence(current, optimal, 2)
        
        # Should be lower confidence
        assert confidence >= 0.0
        assert confidence < 0.7
    
    def test_create_no_optimization_result(self, mock_dependencies):
        """Test creating result when no optimization is possible"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        result = optimizer._create_no_optimization_result(30)
        
        assert result.best_time_minutes_from_now == 0
        assert result.original_eta_minutes == 30
        assert result.optimized_eta_minutes == 30
        assert result.time_saved_minutes == 0
        assert result.cameras_analyzed == 0
        assert result.confidence_score == 0.0
    
    def test_find_optimal_departure_no_cameras(self, mock_dependencies):
        """Test finding optimal departure when no cameras are found"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock no cameras found
        mock_dependencies['camera_loader'].load_cameras.return_value = []
        mock_dependencies['geospatial_service'].find_cameras_along_route.return_value = []
        
        # Route
        route_points = [
            Point(latitude=1.35, longitude=103.82),
            Point(latitude=1.36, longitude=103.83)
        ]
        
        # Find optimal
        result = optimizer.find_optimal_departure(route_points, 30)
        
        # Should return no optimization result
        assert result.cameras_analyzed == 0
        assert result.confidence_score == 0.0
        assert result.time_saved_minutes == 0
    
    def test_find_optimal_departure_success(self, mock_dependencies):
        """Test finding optimal departure - full integration"""
        optimizer = DepartureTimeOptimizer(**mock_dependencies)
        
        # Mock cameras
        camera1 = Camera(camera_id="1001", latitude=1.35, longitude=103.82)
        camera2 = Camera(camera_id="1002", latitude=1.36, longitude=103.83)
        mock_dependencies['camera_loader'].load_cameras.return_value = [camera1, camera2]
        mock_dependencies['geospatial_service'].find_cameras_along_route.return_value = [
            (camera1, 0.2),
            (camera2, 0.4)
        ]
        
        # Mock current CI (high)
        mock_dependencies['repository'].get_latest_ci.side_effect = [0.7, 0.8]
        
        # Mock forecasts (improving traffic)
        # Current (0 min): 0.7, 0.8 (high)
        # +10 min: 0.4, 0.5 (moderate)
        # +20 min: 0.3, 0.4 (light)
        forecast_mocks = []
        for ci_value in [0.7, 0.8, 0.4, 0.5, 0.3, 0.4]:
            mock_forecast = Mock()
            mock_forecast.ci = ci_value
            forecast_mocks.append(mock_forecast)
        
        mock_dependencies['repository'].get_forecast.side_effect = forecast_mocks
        
        # Mock ETA strategy
        mock_dependencies['eta_strategy'].calculate_eta_from_ci.side_effect = [
            45,  # Current ETA (high traffic)
            38,  # Optimal ETA (moderate traffic)
        ]
        
        # Route
        route_points = [
            Point(latitude=1.35, longitude=103.82),
            Point(latitude=1.36, longitude=103.83)
        ]
        
        # Find optimal (only check first 3 time slots)
        result = optimizer.find_optimal_departure(
            route_points, 
            30, 
            forecast_horizon_minutes=20, 
            time_interval_minutes=10
        )
        
        # Assertions
        assert result.cameras_analyzed == 2
        assert result.best_time_minutes_from_now in [0, 10, 20]
        assert result.original_eta_minutes == 30
        assert result.confidence_score > 0.0


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=domain.departure_time_optimizer", "--cov-report=html"])
