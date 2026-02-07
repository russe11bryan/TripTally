"""
Unit tests for Report domain models.
"""
import pytest
from datetime import datetime
from app.models.report import Report, IncidentReport, TechnicalReport


class TestReport:
    """Tests for Report model"""
    
    def test_create_report(self):
        """Test creating a basic Report"""
        report = Report(
            id=1,
            user_id=100,
            status="open"
        )
        
        assert report.id == 1
        assert report.user_id == 100
        assert report.status == "open"
        assert report.type == "report"
    
    def test_report_with_timestamp(self):
        """Test Report with timestamp"""
        now = datetime.now()
        report = Report(
            id=1,
            user_id=100,
            time=now,
            status="resolved"
        )
        
        assert report.time == now
        assert report.status == "resolved"
    
    def test_report_defaults(self):
        """Test Report default values"""
        report = Report(id=1)
        
        assert report.user_id is None
        assert report.time is None
        assert report.status == "open"
        assert report.type == "report"


class TestIncidentReport:
    """Tests for IncidentReport model"""
    
    def test_create_incident_report(self):
        """Test creating an IncidentReport"""
        report = IncidentReport(
            id=1,
            user_id=100,
            start_location_id=200,
            end_location_id=300,
            obstruction_type="road_closure",
            description="Road blocked due to accident",
            resolved=False
        )
        
        assert report.id == 1
        assert report.user_id == 100
        assert report.start_location_id == 200
        assert report.end_location_id == 300
        assert report.obstruction_type == "road_closure"
        assert report.description == "Road blocked due to accident"
        assert report.resolved is False
        assert report.type == "incident"
    
    def test_incident_report_resolved(self):
        """Test IncidentReport when resolved"""
        report = IncidentReport(
            id=1,
            obstruction_type="pothole",
            description="Large pothole on main road",
            resolved=True,
            status="closed"
        )
        
        assert report.resolved is True
        assert report.status == "closed"
    
    def test_incident_report_defaults(self):
        """Test IncidentReport default values"""
        report = IncidentReport(id=1)
        
        assert report.start_location_id is None
        assert report.end_location_id is None
        assert report.obstruction_type == ""
        assert report.description == ""
        assert report.resolved is False
        assert report.status == "open"
        assert report.type == "incident"
    
    def test_incident_report_inheritance(self):
        """Test that IncidentReport inherits from Report"""
        now = datetime.now()
        report = IncidentReport(
            id=1,
            user_id=100,
            time=now,
            status="in_progress",
            obstruction_type="construction",
            description="Road construction"
        )
        
        # Should have all Report properties
        assert report.id == 1
        assert report.user_id == 100
        assert report.time == now
        assert report.status == "in_progress"
        
        # Plus IncidentReport properties
        assert report.obstruction_type == "construction"
        assert report.description == "Road construction"


class TestTechnicalReport:
    """Tests for TechnicalReport model"""
    
    def test_create_technical_report(self):
        """Test creating a TechnicalReport"""
        report = TechnicalReport(
            id=1,
            user_id=100,
            description="App crashes when viewing routes",
            status="open"
        )
        
        assert report.id == 1
        assert report.user_id == 100
        assert report.description == "App crashes when viewing routes"
        assert report.status == "open"
        assert report.type == "technical"
    
    def test_technical_report_with_timestamp(self):
        """Test TechnicalReport with timestamp"""
        now = datetime.now()
        report = TechnicalReport(
            id=1,
            time=now,
            description="Login button not working"
        )
        
        assert report.time == now
        assert report.description == "Login button not working"
    
    def test_technical_report_defaults(self):
        """Test TechnicalReport default values"""
        report = TechnicalReport(id=1)
        
        assert report.description == ""
        assert report.status == "open"
        assert report.type == "technical"
        assert report.user_id is None
        assert report.time is None
