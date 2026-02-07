"""
Unit tests for Route domain models.
"""
import pytest
from app.models.route import Route, UserSuggestedRoute


class TestRoute:
    """Tests for Route model"""
    
    def test_create_route(self):
        """Test creating a basic Route"""
        route = Route(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            transport_mode="driving"
        )
        
        assert route.id == 1
        assert route.start_location_id == 100
        assert route.end_location_id == 200
        assert route.subtype == "recommended"
        assert route.transport_mode == "driving"
        assert route.type == "route"
    
    def test_route_with_route_line(self):
        """Test Route with route_line (list of location IDs)"""
        route = Route(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="alternate",
            route_line=[100, 105, 110, 200]
        )
        
        assert route.route_line == [100, 105, 110, 200]
        assert len(route.route_line) == 4
    
    def test_route_with_metrics(self):
        """Test Route with metrics_id"""
        route = Route(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            metrics_id=500
        )
        
        assert route.metrics_id == 500
    
    def test_route_defaults(self):
        """Test Route default values"""
        route = Route(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended"
        )
        
        assert route.transport_mode == ""
        assert route.route_line == []
        assert route.metrics_id is None
        assert route.type == "route"


class TestUserSuggestedRoute:
    """Tests for UserSuggestedRoute model"""
    
    def test_create_user_suggested_route(self):
        """Test creating a UserSuggestedRoute"""
        route = UserSuggestedRoute(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="user_suggested",
            user_id=42,
            transport_mode="cycling"
        )
        
        assert route.id == 1
        assert route.user_id == 42
        assert route.subtype == "user_suggested"
        assert route.transport_mode == "cycling"
        assert route.type == "user_suggested"
    
    def test_user_suggested_route_without_user(self):
        """Test UserSuggestedRoute without user_id"""
        route = UserSuggestedRoute(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="user_suggested"
        )
        
        assert route.user_id is None
    
    def test_user_suggested_route_inheritance(self):
        """Test that UserSuggestedRoute inherits from Route"""
        route = UserSuggestedRoute(
            id=1,
            start_location_id=100,
            end_location_id=200,
            subtype="user_suggested",
            user_id=42,
            route_line=[100, 150, 200],
            metrics_id=999
        )
        
        # Should have all Route properties
        assert route.start_location_id == 100
        assert route.end_location_id == 200
        assert route.route_line == [100, 150, 200]
        assert route.metrics_id == 999
        
        # Plus UserSuggestedRoute properties
        assert route.user_id == 42
