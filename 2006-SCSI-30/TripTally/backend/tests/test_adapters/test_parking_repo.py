"""
Integration tests for Parking repository adapters.
Tests SqlCarparkRepo and SqlBikeSharingRepo.
"""
import pytest
from app.models.parking import Carpark, BikeSharingPoint
from app.adapters.sqlalchemy_parking_repo import SqlCarparkRepo, SqlBikeSharingRepo


class TestSqlCarparkRepo:
    """Tests for SqlCarparkRepo adapter"""
    
    def test_add_carpark(self, test_db_session):
        """Test adding a new carpark"""
        repo = SqlCarparkRepo(test_db_session)
        
        carpark = Carpark(
            id=0,
            location_id=100,
            hourly_rate=3.50,
            availability=45
        )
        
        result = repo.add(carpark)
        
        assert result.id > 0
        assert result.location_id == 100
        assert result.hourly_rate == 3.50
        assert result.availability == 45
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving carpark by ID"""
        repo = SqlCarparkRepo(test_db_session)
        
        # Add a carpark
        carpark = Carpark(id=0, location_id=100, hourly_rate=5.00, availability=20)
        added = repo.add(carpark)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.hourly_rate == 5.00
        assert found.availability == 20
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent carpark"""
        repo = SqlCarparkRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_carparks(self, test_db_session):
        """Test listing all carparks"""
        repo = SqlCarparkRepo(test_db_session)
        
        # Add multiple carparks
        carpark1 = Carpark(id=0, location_id=100, hourly_rate=3.00, availability=30)
        carpark2 = Carpark(id=0, location_id=200, hourly_rate=4.00, availability=40)
        
        repo.add(carpark1)
        repo.add(carpark2)
        
        # List all
        carparks = repo.list()
        
        assert len(carparks) >= 2
    
    def test_list_by_location(self, test_db_session):
        """Test listing carparks by location"""
        repo = SqlCarparkRepo(test_db_session)
        
        # Add carparks at different locations
        carpark1 = Carpark(id=0, location_id=100, hourly_rate=3.00, availability=30)
        carpark2 = Carpark(id=0, location_id=100, hourly_rate=4.00, availability=40)
        carpark3 = Carpark(id=0, location_id=200, hourly_rate=5.00, availability=50)
        
        repo.add(carpark1)
        repo.add(carpark2)
        repo.add(carpark3)
        
        # Get carparks at location 100
        location_carparks = repo.list_by_location(100)
        
        assert len(location_carparks) == 2
        assert all(c.location_id == 100 for c in location_carparks)
    
    def test_update_carpark(self, test_db_session):
        """Test updating a carpark"""
        repo = SqlCarparkRepo(test_db_session)
        
        # Add a carpark
        carpark = Carpark(id=0, location_id=100, hourly_rate=3.00, availability=50)
        added = repo.add(carpark)
        
        # Update it
        added.hourly_rate = 4.50
        added.availability = 30
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.hourly_rate == 4.50
        assert updated.availability == 30
    
    def test_delete_carpark(self, test_db_session):
        """Test deleting a carpark"""
        repo = SqlCarparkRepo(test_db_session)
        
        # Add a carpark
        carpark = Carpark(id=0, location_id=100, hourly_rate=3.00, availability=40)
        added = repo.add(carpark)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_carpark(self, test_db_session):
        """Test deleting non-existent carpark"""
        repo = SqlCarparkRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_carpark_full(self, test_db_session):
        """Test carpark when full (availability = 0)"""
        repo = SqlCarparkRepo(test_db_session)
        
        carpark = Carpark(id=0, location_id=100, hourly_rate=5.00, availability=0)
        added = repo.add(carpark)
        
        found = repo.get_by_id(added.id)
        assert found.availability == 0


class TestSqlBikeSharingRepo:
    """Tests for SqlBikeSharingRepo adapter"""
    
    def test_add_bike_sharing_point(self, test_db_session):
        """Test adding a new bike sharing point"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        point = BikeSharingPoint(
            id=0,
            location_id=200,
            bikes_available=10
        )
        
        result = repo.add(point)
        
        assert result.id > 0
        assert result.location_id == 200
        assert result.bikes_available == 10
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving bike sharing point by ID"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        # Add a point
        point = BikeSharingPoint(id=0, location_id=200, bikes_available=15)
        added = repo.add(point)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.bikes_available == 15
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent bike sharing point"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_bike_sharing_points(self, test_db_session):
        """Test listing all bike sharing points"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        # Add multiple points
        point1 = BikeSharingPoint(id=0, location_id=200, bikes_available=10)
        point2 = BikeSharingPoint(id=0, location_id=300, bikes_available=20)
        
        repo.add(point1)
        repo.add(point2)
        
        # List all
        points = repo.list()
        
        assert len(points) >= 2
    
    def test_list_by_location(self, test_db_session):
        """Test listing bike sharing points by location"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        # Add points at different locations
        point1 = BikeSharingPoint(id=0, location_id=200, bikes_available=10)
        point2 = BikeSharingPoint(id=0, location_id=200, bikes_available=15)
        point3 = BikeSharingPoint(id=0, location_id=300, bikes_available=20)
        
        repo.add(point1)
        repo.add(point2)
        repo.add(point3)
        
        # Get points at location 200
        location_points = repo.list_by_location(200)
        
        assert len(location_points) == 2
        assert all(p.location_id == 200 for p in location_points)
    
    def test_update_bike_sharing_point(self, test_db_session):
        """Test updating a bike sharing point"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        # Add a point
        point = BikeSharingPoint(id=0, location_id=200, bikes_available=10)
        added = repo.add(point)
        
        # Update it
        added.bikes_available = 5
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.bikes_available == 5
    
    def test_delete_bike_sharing_point(self, test_db_session):
        """Test deleting a bike sharing point"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        # Add a point
        point = BikeSharingPoint(id=0, location_id=200, bikes_available=10)
        added = repo.add(point)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_point(self, test_db_session):
        """Test deleting non-existent bike sharing point"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_bike_sharing_point_empty(self, test_db_session):
        """Test bike sharing point with no bikes"""
        repo = SqlBikeSharingRepo(test_db_session)
        
        point = BikeSharingPoint(id=0, location_id=200, bikes_available=0)
        added = repo.add(point)
        
        found = repo.get_by_id(added.id)
        assert found.bikes_available == 0
