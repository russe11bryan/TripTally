"""
Unit tests for Metrics domain models.
"""
import pytest
from app.models.metrics import (
    Metrics, DrivingMetrics, PTMetrics, 
    WalkingMetrics, CyclingMetrics
)


class TestMetrics:
    """Tests for Metrics model"""
    
    def test_create_metrics(self):
        """Test creating basic Metrics"""
        metrics = Metrics(
            id=1,
            total_cost=15.50,
            total_time_min=45.0,
            total_distance_km=12.5,
            carbon_kg=2.3
        )
        
        assert metrics.id == 1
        assert metrics.total_cost == 15.50
        assert metrics.total_time_min == 45.0
        assert metrics.total_distance_km == 12.5
        assert metrics.carbon_kg == 2.3
        assert metrics.type == "metrics"
    
    def test_metrics_defaults(self):
        """Test Metrics default values"""
        metrics = Metrics(id=1)
        
        assert metrics.total_cost == 0.0
        assert metrics.total_time_min == 0.0
        assert metrics.total_distance_km == 0.0
        assert metrics.carbon_kg == 0.0
        assert metrics.type == "metrics"
    
    def test_metrics_zero_carbon(self):
        """Test Metrics with zero carbon emission"""
        metrics = Metrics(
            id=1,
            total_cost=0.0,
            total_time_min=30.0,
            total_distance_km=5.0,
            carbon_kg=0.0
        )
        
        assert metrics.carbon_kg == 0.0


class TestDrivingMetrics:
    """Tests for DrivingMetrics model"""
    
    def test_create_driving_metrics(self):
        """Test creating DrivingMetrics"""
        metrics = DrivingMetrics(
            id=1,
            total_cost=20.00,
            total_time_min=30.0,
            total_distance_km=25.0,
            carbon_kg=5.5,
            fuel_usage_per_km=0.08,
            fuel_cost_per_liter=2.50,
            fuel_liters=2.0
        )
        
        assert metrics.id == 1
        assert metrics.total_cost == 20.00
        assert metrics.fuel_usage_per_km == 0.08
        assert metrics.fuel_cost_per_liter == 2.50
        assert metrics.fuel_liters == 2.0
        assert metrics.type == "driving"
    
    def test_driving_metrics_defaults(self):
        """Test DrivingMetrics default values"""
        metrics = DrivingMetrics(id=1)
        
        assert metrics.fuel_usage_per_km == 0.0
        assert metrics.fuel_cost_per_liter == 0.0
        assert metrics.fuel_liters == 0.0
        assert metrics.type == "driving"
    
    def test_driving_metrics_inheritance(self):
        """Test that DrivingMetrics inherits from Metrics"""
        metrics = DrivingMetrics(
            id=1,
            total_cost=25.00,
            total_time_min=40.0,
            total_distance_km=30.0,
            carbon_kg=6.0,
            fuel_liters=2.5
        )
        
        # Should have all Metrics properties
        assert metrics.total_cost == 25.00
        assert metrics.total_time_min == 40.0
        assert metrics.total_distance_km == 30.0
        assert metrics.carbon_kg == 6.0
        
        # Plus DrivingMetrics properties
        assert metrics.fuel_liters == 2.5


class TestPTMetrics:
    """Tests for PTMetrics (Public Transport) model"""
    
    def test_create_pt_metrics(self):
        """Test creating PTMetrics"""
        metrics = PTMetrics(
            id=1,
            total_cost=5.50,
            total_time_min=45.0,
            total_distance_km=15.0,
            carbon_kg=1.2,
            busFares=2.00,
            mrtFares=3.50,
            fares=5.50
        )
        
        assert metrics.id == 1
        assert metrics.total_cost == 5.50
        assert metrics.busFares == 2.00
        assert metrics.mrtFares == 3.50
        assert metrics.fares == 5.50
        assert metrics.type == "public_transport"
    
    def test_pt_metrics_bus_only(self):
        """Test PTMetrics with bus only"""
        metrics = PTMetrics(
            id=1,
            busFares=3.00,
            mrtFares=0.0,
            fares=3.00
        )
        
        assert metrics.busFares == 3.00
        assert metrics.mrtFares == 0.0
        assert metrics.fares == 3.00
    
    def test_pt_metrics_defaults(self):
        """Test PTMetrics default values"""
        metrics = PTMetrics(id=1)
        
        assert metrics.busFares == 0.0
        assert metrics.mrtFares == 0.0
        assert metrics.fares == 0.0
        assert metrics.type == "public_transport"


class TestWalkingMetrics:
    """Tests for WalkingMetrics model"""
    
    def test_create_walking_metrics(self):
        """Test creating WalkingMetrics"""
        metrics = WalkingMetrics(
            id=1,
            total_cost=0.0,
            total_time_min=20.0,
            total_distance_km=1.5,
            carbon_kg=0.0,
            calories=150.0
        )
        
        assert metrics.id == 1
        assert metrics.total_cost == 0.0
        assert metrics.calories == 150.0
        assert metrics.carbon_kg == 0.0
        assert metrics.type == "walking"
    
    def test_walking_metrics_defaults(self):
        """Test WalkingMetrics default values"""
        metrics = WalkingMetrics(id=1)
        
        assert metrics.calories == 0.0
        assert metrics.type == "walking"
        assert metrics.total_cost == 0.0  # Walking is free
        assert metrics.carbon_kg == 0.0  # Walking has no emissions
    
    def test_walking_metrics_long_distance(self):
        """Test WalkingMetrics for long distance"""
        metrics = WalkingMetrics(
            id=1,
            total_time_min=90.0,
            total_distance_km=5.0,
            calories=450.0
        )
        
        assert metrics.total_time_min == 90.0
        assert metrics.total_distance_km == 5.0
        assert metrics.calories == 450.0


class TestCyclingMetrics:
    """Tests for CyclingMetrics model"""
    
    def test_create_cycling_metrics(self):
        """Test creating CyclingMetrics"""
        metrics = CyclingMetrics(
            id=1,
            total_cost=0.0,
            total_time_min=15.0,
            total_distance_km=5.0,
            carbon_kg=0.0,
            calories=200.0
        )
        
        assert metrics.id == 1
        assert metrics.total_cost == 0.0
        assert metrics.calories == 200.0
        assert metrics.carbon_kg == 0.0
        assert metrics.type == "cycling"
    
    def test_cycling_metrics_defaults(self):
        """Test CyclingMetrics default values"""
        metrics = CyclingMetrics(id=1)
        
        assert metrics.calories == 0.0
        assert metrics.type == "cycling"
        assert metrics.total_cost == 0.0  # Cycling is free
        assert metrics.carbon_kg == 0.0  # Cycling has no emissions
    
    def test_cycling_metrics_long_ride(self):
        """Test CyclingMetrics for long ride"""
        metrics = CyclingMetrics(
            id=1,
            total_time_min=60.0,
            total_distance_km=20.0,
            calories=600.0
        )
        
        assert metrics.total_time_min == 60.0
        assert metrics.total_distance_km == 20.0
        assert metrics.calories == 600.0
