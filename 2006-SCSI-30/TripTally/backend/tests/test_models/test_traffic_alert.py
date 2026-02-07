"""
Unit tests for TrafficAlert domain model.
"""
import pytest
from datetime import datetime
from app.models.traffic_alert import TrafficAlert


class TestTrafficAlert:
    """Tests for TrafficAlert model"""
    
    def test_create_traffic_alert(self):
        """Test creating a TrafficAlert"""
        alert = TrafficAlert(
            id=1,
            alert_id="ALERT-2025-001",
            location="PIE Eastbound near Exit 32",
            obstruction_type="accident",
            description="Multi-vehicle accident blocking 2 lanes",
            delay_duration=45.0,
            status="active"
        )
        
        assert alert.id == 1
        assert alert.alert_id == "ALERT-2025-001"
        assert alert.location == "PIE Eastbound near Exit 32"
        assert alert.obstruction_type == "accident"
        assert alert.description == "Multi-vehicle accident blocking 2 lanes"
        assert alert.delay_duration == 45.0
        assert alert.status == "active"
    
    def test_traffic_alert_with_timestamps(self):
        """Test TrafficAlert with created and resolved timestamps"""
        created = datetime.now()
        resolved = datetime(2025, 10, 20, 15, 30)
        
        alert = TrafficAlert(
            id=1,
            alert_id="ALERT-2025-002",
            location="CTE Southbound",
            obstruction_type="road_work",
            description="Road maintenance",
            status="resolved",
            created_at=created,
            resolved_at=resolved
        )
        
        assert alert.created_at == created
        assert alert.resolved_at == resolved
        assert alert.status == "resolved"
    
    def test_traffic_alert_defaults(self):
        """Test TrafficAlert default values"""
        alert = TrafficAlert(
            id=1,
            alert_id="ALERT-2025-003",
            location="AYE Westbound",
            obstruction_type="heavy_traffic",
            description="Heavy traffic due to weather"
        )
        
        assert alert.delay_duration is None
        assert alert.status == "active"
        assert alert.created_at is None
        assert alert.resolved_at is None
    
    def test_traffic_alert_no_delay(self):
        """Test TrafficAlert without delay duration"""
        alert = TrafficAlert(
            id=1,
            alert_id="ALERT-2025-004",
            location="BKE Northbound",
            obstruction_type="stalled_vehicle",
            description="Stalled vehicle on shoulder",
            delay_duration=None
        )
        
        assert alert.delay_duration is None
    
    def test_traffic_alert_expired(self):
        """Test TrafficAlert with expired status"""
        alert = TrafficAlert(
            id=1,
            alert_id="ALERT-2025-005",
            location="ECP Eastbound",
            obstruction_type="accident",
            description="Minor accident - cleared",
            status="expired"
        )
        
        assert alert.status == "expired"
    
    def test_traffic_alert_various_obstruction_types(self):
        """Test TrafficAlert with different obstruction types"""
        types = ["accident", "road_work", "heavy_traffic", "stalled_vehicle", "weather"]
        
        for idx, obs_type in enumerate(types, 1):
            alert = TrafficAlert(
                id=idx,
                alert_id=f"ALERT-{idx}",
                location=f"Location {idx}",
                obstruction_type=obs_type,
                description=f"Description for {obs_type}"
            )
            
            assert alert.obstruction_type == obs_type
