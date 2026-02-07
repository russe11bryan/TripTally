"""
Integration tests for SqlRouteRepo adapter.
Tests the SQLAlchemy implementation of RouteRepository.
"""
import pytest
from app.models.route import Route, UserSuggestedRoute
from app.adapters.sqlalchemy_route_repo import SqlRouteRepo


class TestSqlRouteRepo:
    """Tests for SqlRouteRepo adapter"""
    
    def test_add_route(self, test_db_session):
        """Test adding a new route"""
        repo = SqlRouteRepo(test_db_session)
        
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            transport_mode="driving"
        )
        
        result = repo.add(route)
        
        assert result.id > 0
        assert result.start_location_id == 100
        assert result.end_location_id == 200
        assert result.subtype == "recommended"
        assert result.transport_mode == "driving"
    
    def test_add_user_suggested_route(self, test_db_session):
        """Test adding a user-suggested route"""
        repo = SqlRouteRepo(test_db_session)
        
        route = UserSuggestedRoute(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="user_suggested",
            transport_mode="cycling",
            user_id=42
        )
        
        result = repo.add(route)
        
        assert result.id > 0
        assert result.user_id == 42
        assert result.subtype == "user_suggested"
        assert result.transport_mode == "cycling"
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving route by ID"""
        repo = SqlRouteRepo(test_db_session)
        
        # Add a route first
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="alternate",
            transport_mode="walking"
        )
        added = repo.add(route)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.start_location_id == 100
        assert found.end_location_id == 200
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent route"""
        repo = SqlRouteRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_routes(self, test_db_session):
        """Test listing all routes"""
        repo = SqlRouteRepo(test_db_session)
        
        # Add multiple routes
        route1 = Route(id=0, start_location_id=100, end_location_id=200, subtype="recommended")
        route2 = Route(id=0, start_location_id=300, end_location_id=400, subtype="alternate")
        
        repo.add(route1)
        repo.add(route2)
        
        # List all
        routes = repo.list()
        
        assert len(routes) >= 2
    
    def test_list_by_user(self, test_db_session):
        """Test listing routes by specific user"""
        repo = SqlRouteRepo(test_db_session)
        
        # Add user-suggested routes
        route1 = UserSuggestedRoute(
            id=0, start_location_id=100, end_location_id=200,
            subtype="user_suggested", user_id=42
        )
        route2 = UserSuggestedRoute(
            id=0, start_location_id=300, end_location_id=400,
            subtype="user_suggested", user_id=42
        )
        route3 = UserSuggestedRoute(
            id=0, start_location_id=500, end_location_id=600,
            subtype="user_suggested", user_id=99
        )
        
        repo.add(route1)
        repo.add(route2)
        repo.add(route3)
        
        # Get routes for user 42
        user_routes = repo.list_by_user(42)
        
        assert len(user_routes) == 2
        assert all(r.user_id == 42 for r in user_routes)
    
    def test_update_route(self, test_db_session):
        """Test updating a route"""
        repo = SqlRouteRepo(test_db_session)
        
        # Add a route
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            transport_mode="driving"
        )
        added = repo.add(route)
        
        # Update it
        added.transport_mode = "cycling"
        added.subtype = "alternate"
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.transport_mode == "cycling"
        assert updated.subtype == "alternate"
    
    def test_delete_route(self, test_db_session):
        """Test deleting a route"""
        repo = SqlRouteRepo(test_db_session)
        
        # Add a route
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended"
        )
        added = repo.add(route)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_route(self, test_db_session):
        """Test deleting non-existent route"""
        repo = SqlRouteRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_route_with_route_line(self, test_db_session):
        """Test route with route_line (list of location IDs)"""
        repo = SqlRouteRepo(test_db_session)
        
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            route_line=[100, 110, 120, 200]
        )
        
        added = repo.add(route)
        found = repo.get_by_id(added.id)
        
        assert found.route_line == [100, 110, 120, 200]
    
    def test_route_with_metrics_id(self, test_db_session):
        """Test route with metrics_id"""
        repo = SqlRouteRepo(test_db_session)
        
        route = Route(
            id=0,
            start_location_id=100,
            end_location_id=200,
            subtype="recommended",
            metrics_id=999
        )
        
        added = repo.add(route)
        found = repo.get_by_id(added.id)
        
        assert found.metrics_id == 999
