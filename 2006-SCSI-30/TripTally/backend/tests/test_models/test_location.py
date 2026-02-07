"""
Tests for LocationNode domain model.
No database needed - pure Python dataclass testing.
"""
import pytest
from app.models.location import LocationNode


class TestLocationNode:
    """Test LocationNode model."""
    
    def test_create_location(self):
        """Test creating a LocationNode instance."""
        location = LocationNode(
            id=1,
            name="NTU Main Gate",
            lat=1.3483,
            lng=103.6831
        )
        
        assert location.id == 1
        assert location.name == "NTU Main Gate"
        assert location.lat == 1.3483
        assert location.lng == 103.6831
    
    def test_location_with_coordinates(self):
        """Test location with specific coordinates."""
        location = LocationNode(
            id=2,
            name="Marina Bay Sands",
            lat=1.2834,
            lng=103.8607
        )
        
        assert location.lat > 0
        assert location.lng > 0
        assert isinstance(location.lat, float)
        assert isinstance(location.lng, float)
    
    def test_location_equality(self):
        """Test that two locations with same data are equal."""
        loc1 = LocationNode(id=1, name="Test", lat=1.0, lng=2.0)
        loc2 = LocationNode(id=1, name="Test", lat=1.0, lng=2.0)
        
        assert loc1 == loc2
    
    def test_location_different_coords(self):
        """Test locations with different coordinates."""
        loc1 = LocationNode(id=1, name="Place A", lat=1.0, lng=2.0)
        loc2 = LocationNode(id=2, name="Place B", lat=3.0, lng=4.0)
        
        assert loc1 != loc2
