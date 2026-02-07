"""
Integration tests for SqlTrafficAlertRepo adapter.
Tests the SQLAlchemy implementation of TrafficAlertRepository.
"""
import pytest
from datetime import datetime
from app.models.traffic_alert import TrafficAlert
from app.adapters.sqlalchemy_traffic_alert_repo import SqlTrafficAlertRepo


class TestSqlTrafficAlertRepo:
    """Tests for SqlTrafficAlertRepo adapter"""
    
    def test_add_traffic_alert(self, test_db_session):
        """Test adding a new traffic alert"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-2025-001",
            location="PIE Eastbound near Exit 32",
            obstruction_type="accident",
            description="Multi-vehicle accident blocking 2 lanes",
            delay_duration=45.0,
            status="active"
        )
        
        result = repo.add(alert)
        
        assert result.id > 0
        assert result.alert_id == "ALERT-2025-001"
        assert result.location == "PIE Eastbound near Exit 32"
        assert result.obstruction_type == "accident"
        assert result.status == "active"
    
    def test_add_alert_with_timestamps(self, test_db_session):
        """Test adding alert with timestamps"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        now = datetime.now()
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-2025-002",
            location="CTE Southbound",
            obstruction_type="road_work",
            description="Road maintenance",
            status="active",
            created_at=now
        )
        
        result = repo.add(alert)
        
        assert result.id > 0
        assert result.created_at is not None
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving alert by database ID"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add an alert
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-2025-003",
            location="AYE Westbound",
            obstruction_type="heavy_traffic",
            description="Heavy traffic due to weather"
        )
        added = repo.add(alert)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.alert_id == "ALERT-2025-003"
        assert found.obstruction_type == "heavy_traffic"
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent alert"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_get_by_alert_id(self, test_db_session):
        """Test retrieving alert by external alert ID"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add an alert
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-2025-UNIQUE",
            location="BKE Northbound",
            obstruction_type="stalled_vehicle",
            description="Stalled vehicle on shoulder"
        )
        repo.add(alert)
        
        # Retrieve by alert_id
        found = repo.get_by_alert_id("ALERT-2025-UNIQUE")
        
        assert found is not None
        assert found.alert_id == "ALERT-2025-UNIQUE"
        assert found.obstruction_type == "stalled_vehicle"
    
    def test_get_by_alert_id_not_found(self, test_db_session):
        """Test retrieving alert by non-existent alert ID"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        result = repo.get_by_alert_id("NONEXISTENT-ID")
        
        assert result is None
    
    def test_list_alerts(self, test_db_session):
        """Test listing all alerts"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add multiple alerts
        alert1 = TrafficAlert(
            id=0, alert_id="ALERT-1", location="Location 1",
            obstruction_type="accident", description="Accident"
        )
        alert2 = TrafficAlert(
            id=0, alert_id="ALERT-2", location="Location 2",
            obstruction_type="road_work", description="Road work"
        )
        
        repo.add(alert1)
        repo.add(alert2)
        
        # List all
        alerts = repo.list()
        
        assert len(alerts) >= 2
    
    def test_list_active_alerts(self, test_db_session):
        """Test listing only active alerts"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add alerts with different statuses
        alert1 = TrafficAlert(
            id=0, alert_id="ALERT-1", location="Location 1",
            obstruction_type="accident", description="Active accident",
            status="active"
        )
        alert2 = TrafficAlert(
            id=0, alert_id="ALERT-2", location="Location 2",
            obstruction_type="road_work", description="Resolved work",
            status="resolved"
        )
        alert3 = TrafficAlert(
            id=0, alert_id="ALERT-3", location="Location 3",
            obstruction_type="heavy_traffic", description="Active traffic",
            status="active"
        )
        
        repo.add(alert1)
        repo.add(alert2)
        repo.add(alert3)
        
        # Get only active alerts
        active_alerts = repo.list_active()
        
        assert len(active_alerts) == 2
        assert all(a.status == "active" for a in active_alerts)
    
    def test_list_by_status(self, test_db_session):
        """Test listing alerts by specific status"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add alerts with different statuses
        alert1 = TrafficAlert(
            id=0, alert_id="ALERT-1", location="L1",
            obstruction_type="accident", description="D1", status="active"
        )
        alert2 = TrafficAlert(
            id=0, alert_id="ALERT-2", location="L2",
            obstruction_type="road_work", description="D2", status="resolved"
        )
        alert3 = TrafficAlert(
            id=0, alert_id="ALERT-3", location="L3",
            obstruction_type="accident", description="D3", status="resolved"
        )
        alert4 = TrafficAlert(
            id=0, alert_id="ALERT-4", location="L4",
            obstruction_type="weather", description="D4", status="expired"
        )
        
        repo.add(alert1)
        repo.add(alert2)
        repo.add(alert3)
        repo.add(alert4)
        
        # Get resolved alerts
        resolved_alerts = repo.list_by_status("resolved")
        
        assert len(resolved_alerts) == 2
        assert all(a.status == "resolved" for a in resolved_alerts)
    
    def test_update_alert(self, test_db_session):
        """Test updating a traffic alert"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add an alert
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-2025-UPDATE",
            location="ECP Eastbound",
            obstruction_type="accident",
            description="Minor accident",
            status="active"
        )
        added = repo.add(alert)
        
        # Update it
        added.status = "resolved"
        added.description = "Accident cleared"
        resolved_time = datetime.now()
        added.resolved_at = resolved_time
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.status == "resolved"
        assert updated.description == "Accident cleared"
        assert updated.resolved_at is not None
    
    def test_delete_alert(self, test_db_session):
        """Test deleting a traffic alert"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        # Add an alert
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-DELETE",
            location="Test Location",
            obstruction_type="test",
            description="Test alert"
        )
        added = repo.add(alert)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_alert(self, test_db_session):
        """Test deleting non-existent alert"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_alert_with_delay_duration(self, test_db_session):
        """Test alert with delay duration"""
        repo = SqlTrafficAlertRepo(test_db_session)
        
        alert = TrafficAlert(
            id=0,
            alert_id="ALERT-DELAY",
            location="Highway 1",
            obstruction_type="accident",
            description="Severe accident",
            delay_duration=120.0  # 2 hours
        )
        
        added = repo.add(alert)
        found = repo.get_by_id(added.id)
        
        assert found.delay_duration == 120.0
