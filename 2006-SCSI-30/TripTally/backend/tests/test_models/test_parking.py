"""
Unit tests for Parking domain models.
"""
import pytest
from app.models.parking import Carpark, BikeSharingPoint


class TestCarpark:
    """Tests for Carpark model"""
    
    def test_create_carpark(self):
        """Test creating a Carpark"""
        carpark = Carpark(
            id=1,
            location_id=100,
            hourly_rate=3.50,
            availability=45
        )
        
        assert carpark.id == 1
        assert carpark.location_id == 100
        assert carpark.hourly_rate == 3.50
        assert carpark.availability == 45
    
    def test_carpark_free_parking(self):
        """Test Carpark with free parking"""
        carpark = Carpark(
            id=1,
            location_id=100,
            hourly_rate=0.0,
            availability=100
        )
        
        assert carpark.hourly_rate == 0.0
        assert carpark.availability == 100
    
    def test_carpark_full(self):
        """Test Carpark when full"""
        carpark = Carpark(
            id=1,
            location_id=100,
            hourly_rate=5.00,
            availability=0
        )
        
        assert carpark.availability == 0
    
    def test_carpark_defaults(self):
        """Test Carpark default values"""
        carpark = Carpark(id=1, location_id=100)
        
        assert carpark.hourly_rate == 0.0
        assert carpark.availability == 0
    
    def test_carpark_high_rate(self):
        """Test Carpark with high hourly rate"""
        carpark = Carpark(
            id=1,
            location_id=100,
            hourly_rate=12.50,
            availability=20
        )
        
        assert carpark.hourly_rate == 12.50


class TestBikeSharingPoint:
    """Tests for BikeSharingPoint model"""
    
    def test_create_bike_sharing_point(self):
        """Test creating a BikeSharingPoint"""
        point = BikeSharingPoint(
            id=1,
            location_id=200,
            bikes_available=10
        )
        
        assert point.id == 1
        assert point.location_id == 200
        assert point.bikes_available == 10
    
    def test_bike_sharing_point_empty(self):
        """Test BikeSharingPoint with no bikes"""
        point = BikeSharingPoint(
            id=1,
            location_id=200,
            bikes_available=0
        )
        
        assert point.bikes_available == 0
    
    def test_bike_sharing_point_full(self):
        """Test BikeSharingPoint at full capacity"""
        point = BikeSharingPoint(
            id=1,
            location_id=200,
            bikes_available=50
        )
        
        assert point.bikes_available == 50
    
    def test_bike_sharing_point_defaults(self):
        """Test BikeSharingPoint default values"""
        point = BikeSharingPoint(id=1, location_id=200)
        
        assert point.bikes_available == 0
