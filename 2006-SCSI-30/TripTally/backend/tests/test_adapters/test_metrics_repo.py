"""
Integration tests for SqlMetricsRepo adapter.
Tests the SQLAlchemy implementation of MetricsRepository.
Note: Metrics models don't have route_id in domain, only in database table.
"""
import pytest
from app.models.metrics import (
    Metrics, DrivingMetrics, PTMetrics,
    WalkingMetrics, CyclingMetrics
)
from app.adapters.sqlalchemy_metrics_repo import SqlMetricsRepo


class TestSqlMetricsRepo:
    """Tests for SqlMetricsRepo adapter"""
    
    def test_add_basic_metrics(self, test_db_session):
        """Test adding basic metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        metrics = Metrics(
            id=0,
            total_cost=15.50,
            total_time_min=45.0,
            total_distance_km=12.5,
            carbon_kg=2.3
        )
        
        result = repo.add(metrics)
        
        assert result.id > 0
        assert result.total_cost == 15.50
        assert result.total_time_min == 45.0
    
    def test_add_driving_metrics(self, test_db_session):
        """Test adding driving metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        metrics = DrivingMetrics(
            id=0,
            total_cost=20.00,
            total_time_min=30.0,
            total_distance_km=25.0,
            carbon_kg=5.5,
            fuel_usage_per_km=0.08,
            fuel_cost_per_liter=2.50,
            fuel_liters=2.0
        )
        
        result = repo.add(metrics)
        
        assert result.id > 0
        assert result.fuel_liters == 2.0
        assert result.fuel_cost_per_liter == 2.50
    
    def test_add_pt_metrics(self, test_db_session):
        """Test adding public transport metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        metrics = PTMetrics(
            id=0,
            total_cost=5.50,
            total_time_min=45.0,
            total_distance_km=15.0,
            carbon_kg=1.2,
            busFares=2.00,
            mrtFares=3.50,
            fares=5.50
        )
        
        result = repo.add(metrics)
        
        assert result.id > 0
        assert result.busFares == 2.00
        assert result.mrtFares == 3.50
        assert result.fares == 5.50
    
    def test_add_walking_metrics(self, test_db_session):
        """Test adding walking metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        metrics = WalkingMetrics(
            id=0,
            total_cost=0.0,
            total_time_min=20.0,
            total_distance_km=1.5,
            carbon_kg=0.0,
            calories=150.0
        )
        
        result = repo.add(metrics)
        
        assert result.id > 0
        assert result.calories == 150.0
        assert result.total_cost == 0.0  # Walking is free
    
    def test_add_cycling_metrics(self, test_db_session):
        """Test adding cycling metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        metrics = CyclingMetrics(
            id=0,
            total_cost=0.0,
            total_time_min=15.0,
            total_distance_km=5.0,
            carbon_kg=0.0,
            calories=200.0
        )
        
        result = repo.add(metrics)
        
        assert result.id > 0
        assert result.calories == 200.0
        assert result.carbon_kg == 0.0
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving metrics by ID"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add metrics
        metrics = DrivingMetrics(
            id=0,
            total_cost=20.00,
            total_distance_km=25.0,
            fuel_liters=2.0
        )
        added = repo.add(metrics)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert isinstance(found, DrivingMetrics)
        assert found.fuel_liters == 2.0
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_metrics(self, test_db_session):
        """Test listing all metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add multiple metrics
        metrics1 = DrivingMetrics(id=0, total_cost=20.00, fuel_liters=2.0)
        metrics2 = WalkingMetrics(id=0, total_cost=0.0, calories=150.0)
        
        repo.add(metrics1)
        repo.add(metrics2)
        
        # List all
        all_metrics = repo.list()
        
        assert len(all_metrics) >= 2
    
    def test_update_driving_metrics(self, test_db_session):
        """Test updating driving metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add metrics
        metrics = DrivingMetrics(
            id=0,
            total_cost=20.00,
            fuel_liters=2.0,
            fuel_cost_per_liter=2.50
        )
        added = repo.add(metrics)
        
        # Update it
        added.total_cost = 25.00
        added.fuel_liters = 2.5
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert isinstance(updated, DrivingMetrics)
        assert updated.total_cost == 25.00
        assert updated.fuel_liters == 2.5
    
    def test_update_pt_metrics(self, test_db_session):
        """Test updating PT metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add metrics
        metrics = PTMetrics(
            id=0,
            total_cost=5.50,
            busFares=2.00,
            mrtFares=3.50,
            fares=5.50
        )
        added = repo.add(metrics)
        
        # Update it
        added.fares = 6.00
        added.total_cost = 6.00
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert isinstance(updated, PTMetrics)
        assert updated.fares == 6.00
    
    def test_delete_metrics(self, test_db_session):
        """Test deleting metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add metrics
        metrics = Metrics(id=0, total_cost=15.00)
        added = repo.add(metrics)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_metrics(self, test_db_session):
        """Test deleting non-existent metrics"""
        repo = SqlMetricsRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_metrics_polymorphism(self, test_db_session):
        """Test that different metric types are properly distinguished"""
        repo = SqlMetricsRepo(test_db_session)
        
        # Add different types
        driving = DrivingMetrics(id=0, total_cost=20.00, fuel_liters=2.0)
        walking = WalkingMetrics(id=0, total_cost=0.0, calories=150.0)
        cycling = CyclingMetrics(id=0, total_cost=0.0, calories=200.0)
        pt = PTMetrics(id=0, total_cost=5.50, fares=5.50)
        
        added_driving = repo.add(driving)
        added_walking = repo.add(walking)
        added_cycling = repo.add(cycling)
        added_pt = repo.add(pt)
        
        # Retrieve and verify types
        found_driving = repo.get_by_id(added_driving.id)
        found_walking = repo.get_by_id(added_walking.id)
        found_cycling = repo.get_by_id(added_cycling.id)
        found_pt = repo.get_by_id(added_pt.id)
        
        assert isinstance(found_driving, DrivingMetrics)
        assert isinstance(found_walking, WalkingMetrics)
        assert isinstance(found_cycling, CyclingMetrics)
        assert isinstance(found_pt, PTMetrics)
