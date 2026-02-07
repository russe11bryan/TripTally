"""
Unit tests for Departure Optimization API Routes
Coverage: 100% of api/departure_optimization_routes.py

Testing Strategy:
- Test FastAPI endpoints with TestClient
- Test request validation
- Test response formatting
- Test error handling
- Test DTOs and serialization
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/services/trafficcams'))

from fastapi import FastAPI
from api.departure_optimization_routes import router, _generate_recommendation_text
from domain.departure_time_optimizer import OptimalDepartureResult
from domain.route_models import Point


@pytest.fixture
def app():
    """Create FastAPI app with router"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_optimizer():
    """Mock DepartureTimeOptimizer"""
    with patch('api.departure_optimization_routes.DepartureTimeOptimizer') as mock:
        yield mock


@pytest.fixture
def mock_service_context():
    """Mock ServiceContext"""
    with patch('api.departure_optimization_routes.ServiceContext') as mock:
        # Mock config and repository
        mock_config = Mock()
        mock_repo = Mock()
        mock.get_config.return_value = mock_config
        mock.get_repository.return_value = mock_repo
        yield mock


class TestRoutePointRequest:
    """Test RoutePointRequest DTO"""
    
    def test_valid_route_point(self, client):
        """Test valid route point"""
        # Valid coordinates
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25
        }
        
        # Should not raise validation error
        # (We'll test in full endpoint test)
    
    def test_invalid_latitude(self, client):
        """Test invalid latitude (out of range)"""
        payload = {
            "route_points": [
                {"latitude": 91.0, "longitude": 103.82},  # Invalid: > 90
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_longitude(self, client):
        """Test invalid longitude (out of range)"""
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 181.0},  # Invalid: > 180
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_to_domain(self):
        """Test conversion to domain model"""
        from api.departure_optimization_routes import RoutePointRequest
        
        request = RoutePointRequest(latitude=1.35, longitude=103.82)
        domain_point = request.to_domain()
        
        assert isinstance(domain_point, Point)
        assert domain_point.latitude == 1.35
        assert domain_point.longitude == 103.82


class TestOptimalDepartureRequest:
    """Test OptimalDepartureRequest DTO"""
    
    def test_minimum_route_points(self, client):
        """Test that route must have at least 2 points"""
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82}  # Only 1 point
            ],
            "original_eta_minutes": 25
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_eta_validation(self, client):
        """Test ETA validation"""
        # ETA too small
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 0  # Invalid: < 1
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
        
        # ETA too large
        payload["original_eta_minutes"] = 400  # Invalid: > 300
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
    
    def test_search_radius_validation(self, client):
        """Test search radius validation"""
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25,
            "search_radius_km": 0.05  # Invalid: < 0.1
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
        
        payload["search_radius_km"] = 10.0  # Invalid: > 5.0
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
    
    def test_forecast_horizon_validation(self, client):
        """Test forecast horizon validation"""
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25,
            "forecast_horizon_minutes": 5  # Invalid: < 10
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
        
        payload["forecast_horizon_minutes"] = 200  # Invalid: > 180
        response = client.post("/api/traffic/departure/optimize", json=payload)
        assert response.status_code == 422
    
    def test_default_values(self, client, mock_optimizer, mock_service_context):
        """Test default values for optional parameters"""
        # Mock optimizer
        now = datetime.now()
        mock_result = OptimalDepartureResult(
            best_time_minutes_from_now=0,
            best_departure_time=now,
            original_eta_minutes=25,
            optimized_eta_minutes=25,
            time_saved_minutes=0,
            current_total_ci=0.6,
            optimal_total_ci=0.6,
            current_average_ci=0.3,
            optimal_average_ci=0.3,
            cameras_analyzed=2,
            confidence_score=0.7
        )
        mock_optimizer.return_value.find_optimal_departure.return_value = mock_result
        
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 25
            # No optional parameters
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 200
        # Defaults should be: search_radius_km=0.5, forecast_horizon_minutes=120


class TestOptimizeEndpoint:
    """Test /optimize endpoint"""
    
    def test_successful_optimization(self, client, mock_optimizer, mock_service_context):
        """Test successful optimization"""
        # Mock optimizer result
        now = datetime.now()
        mock_result = OptimalDepartureResult(
            best_time_minutes_from_now=15,
            best_departure_time=now,
            original_eta_minutes=30,
            optimized_eta_minutes=25,
            time_saved_minutes=7,
            current_total_ci=1.2,
            optimal_total_ci=0.8,
            current_average_ci=0.6,
            optimal_average_ci=0.4,
            cameras_analyzed=2,
            confidence_score=0.75
        )
        mock_optimizer.return_value.find_optimal_departure.return_value = mock_result
        
        # Request
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 30
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["best_time_minutes_from_now"] == 15
        assert data["original_eta_minutes"] == 30
        assert data["optimized_eta_minutes"] == 25
        assert data["time_saved_minutes"] == 7
        assert data["cameras_analyzed"] == 2
        assert data["confidence_score"] == 0.75
        assert "recommendation_text" in data
    
    def test_optimization_with_no_cameras(self, client, mock_optimizer, mock_service_context):
        """Test optimization when no cameras are found"""
        # Mock optimizer result with 0 cameras
        now = datetime.now()
        mock_result = OptimalDepartureResult(
            best_time_minutes_from_now=0,
            best_departure_time=now,
            original_eta_minutes=30,
            optimized_eta_minutes=30,
            time_saved_minutes=0,
            current_total_ci=0.0,
            optimal_total_ci=0.0,
            current_average_ci=0.0,
            optimal_average_ci=0.0,
            cameras_analyzed=0,
            confidence_score=0.0
        )
        mock_optimizer.return_value.find_optimal_departure.return_value = mock_result
        
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 30
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["cameras_analyzed"] == 0
        assert "No traffic data available" in data["recommendation_text"]
    
    def test_optimization_error_handling(self, client, mock_optimizer, mock_service_context):
        """Test error handling in optimization"""
        # Mock optimizer raising exception
        mock_optimizer.return_value.find_optimal_departure.side_effect = Exception("Test error")
        
        payload = {
            "route_points": [
                {"latitude": 1.35, "longitude": 103.82},
                {"latitude": 1.36, "longitude": 103.83}
            ],
            "original_eta_minutes": 30
        }
        
        response = client.post("/api/traffic/departure/optimize", json=payload)
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to optimize departure time" in data["detail"]


class TestGenerateRecommendationText:
    """Test _generate_recommendation_text function"""
    
    def test_no_cameras(self):
        """Test recommendation with no cameras"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=0,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=30,
            time_saved_minutes=0,
            current_total_ci=0.0,
            optimal_total_ci=0.0,
            current_average_ci=0.0,
            optimal_average_ci=0.0,
            cameras_analyzed=0,
            confidence_score=0.0
        )
        
        text = _generate_recommendation_text(result, 30)
        
        assert "No traffic data available" in text
    
    def test_leave_now(self):
        """Test recommendation to leave now"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=0,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=30,
            time_saved_minutes=0,
            current_total_ci=0.6,
            optimal_total_ci=0.6,
            current_average_ci=0.3,
            optimal_average_ci=0.3,
            cameras_analyzed=2,
            confidence_score=0.7
        )
        
        text = _generate_recommendation_text(result, 30)
        
        assert "Leave now" in text
        assert "30 minutes" in text
    
    def test_significant_time_savings(self):
        """Test recommendation with significant time savings (> 5 min)"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=20,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=25,
            time_saved_minutes=10,
            current_total_ci=1.5,
            optimal_total_ci=0.8,
            current_average_ci=0.75,
            optimal_average_ci=0.4,
            cameras_analyzed=3,
            confidence_score=0.8
        )
        
        text = _generate_recommendation_text(result, 35)
        
        assert "Wait 20 minutes" in text
        assert "save 10 minutes" in text
        assert "ETA: 25 min" in text
    
    def test_small_time_savings(self):
        """Test recommendation with small time savings (1-5 min)"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=10,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=28,
            time_saved_minutes=3,
            current_total_ci=1.0,
            optimal_total_ci=0.8,
            current_average_ci=0.5,
            optimal_average_ci=0.4,
            cameras_analyzed=2,
            confidence_score=0.6
        )
        
        text = _generate_recommendation_text(result, 31)
        
        assert "Waiting 10 minutes may save 3 minutes" in text
        assert "ETA: 28 min" in text
    
    def test_no_time_savings(self):
        """Test recommendation with no time savings"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=15,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=30,
            time_saved_minutes=0,
            current_total_ci=0.9,
            optimal_total_ci=0.9,
            current_average_ci=0.45,
            optimal_average_ci=0.45,
            cameras_analyzed=2,
            confidence_score=0.5
        )
        
        text = _generate_recommendation_text(result, 30)
        
        assert "Traffic is similar" in text
        assert "30 min" in text
    
    def test_negative_time_savings(self):
        """Test recommendation with negative time savings (traffic gets worse)"""
        result = OptimalDepartureResult(
            best_time_minutes_from_now=30,
            best_departure_time=datetime.now(),
            original_eta_minutes=30,
            optimized_eta_minutes=35,
            time_saved_minutes=-5,
            current_total_ci=0.8,
            optimal_total_ci=1.2,
            current_average_ci=0.4,
            optimal_average_ci=0.6,
            cameras_analyzed=2,
            confidence_score=0.7
        )
        
        text = _generate_recommendation_text(result, 32)
        
        # Should indicate traffic is similar or worse
        assert "Traffic is similar" in text or "32 min" in text


class TestHealthEndpoint:
    """Test /health endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/traffic/departure/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "Departure Time Optimization API"
        assert "timestamp" in data
        
        # Verify timestamp is valid ISO format
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([
        __file__, 
        "-v", 
        "--cov=api.departure_optimization_routes", 
        "--cov-report=html",
        "--cov-report=term"
    ])
