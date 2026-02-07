"""
Tests for Location repository adapter.
Uses SQLite in-memory database for testing.
"""
import pytest
from app.models.location import LocationNode
from app.adapters.sqlalchemy_location_repo import SqlLocationRepo


class TestSqlLocationRepo:
    """Test SqlLocationRepo adapter with in-memory database."""
    
    def test_add_location(self, test_db_session):
        """Test adding a location to the database."""
        repo = SqlLocationRepo(test_db_session)
        
        location = LocationNode(
            id=0,
            name="NTU Main Gate",
            lat=1.3483,
            lng=103.6831
        )
        
        saved = repo.add(location)
        
        assert saved.id > 0
        assert saved.name == "NTU Main Gate"
        assert saved.lat == 1.3483
        assert saved.lng == 103.6831
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving location by ID."""
        repo = SqlLocationRepo(test_db_session)
        
        location = LocationNode(
            id=0,
            name="Marina Bay Sands",
            lat=1.2834,
            lng=103.8607
        )
        saved = repo.add(location)
        
        retrieved = repo.get_by_id(saved.id)
        
        assert retrieved is not None
        assert retrieved.name == "Marina Bay Sands"
        assert retrieved.lat == 1.2834
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent location returns None."""
        repo = SqlLocationRepo(test_db_session)
        
        location = repo.get_by_id(9999)
        
        assert location is None
    
    def test_list_locations(self, test_db_session):
        """Test listing all locations."""
        repo = SqlLocationRepo(test_db_session)
        
        # Add multiple locations
        locations_data = [
            ("NTU", 1.3483, 103.6831),
            ("NUS", 1.2966, 103.7764),
            ("SMU", 1.2951, 103.8500)
        ]
        
        for name, lat, lng in locations_data:
            location = LocationNode(id=0, name=name, lat=lat, lng=lng)
            repo.add(location)
        
        locations = repo.list()
        
        assert len(locations) == 3
        assert all(isinstance(loc, LocationNode) for loc in locations)
    
    def test_update_location(self, test_db_session):
        """Test updating a location."""
        repo = SqlLocationRepo(test_db_session)
        
        location = LocationNode(
            id=0,
            name="Old Name",
            lat=1.0,
            lng=2.0
        )
        saved = repo.add(location)
        
        # Update location
        saved.name = "New Name"
        saved.lat = 1.5
        saved.lng = 2.5
        repo.update(saved)
        
        # Verify update
        retrieved = repo.get_by_id(saved.id)
        assert retrieved.name == "New Name"
        assert retrieved.lat == 1.5
        assert retrieved.lng == 2.5
    
    def test_delete_location(self, test_db_session):
        """Test deleting a location."""
        repo = SqlLocationRepo(test_db_session)
        
        location = LocationNode(
            id=0,
            name="Delete Me",
            lat=1.0,
            lng=2.0
        )
        saved = repo.add(location)
        location_id = saved.id
        
        # Delete
        result = repo.delete(location_id)
        assert result is True
        
        # Verify deleted
        retrieved = repo.get_by_id(location_id)
        assert retrieved is None
    
    def test_delete_nonexistent_location(self, test_db_session):
        """Test deleting non-existent location returns False."""
        repo = SqlLocationRepo(test_db_session)
        
        result = repo.delete(9999)
        assert result is False
