"""
Integration tests for SqlReportRepo adapter.
Tests the SQLAlchemy implementation of ReportRepository.
"""
import pytest
from datetime import datetime
from app.models.report import Report, IncidentReport, TechnicalReport
from app.adapters.sqlalchemy_report_repo import SqlReportRepo


class TestSqlReportRepo:
    """Tests for SqlReportRepo adapter"""
    
    def test_add_report(self, test_db_session):
        """Test adding a basic report"""
        repo = SqlReportRepo(test_db_session)
        
        report = Report(
            id=0,
            user_id=100,
            status="open"
        )
        
        result = repo.add(report)
        
        assert result.id > 0
        assert result.user_id == 100
    
    def test_add_incident_report(self, test_db_session):
        """Test adding an incident report"""
        repo = SqlReportRepo(test_db_session)
        
        report = IncidentReport(
            id=0,
            user_id=100,
            start_location_id=200,
            end_location_id=300,
            obstruction_type="road_closure",
            description="Road blocked due to accident",
            resolved=False
        )
        
        result = repo.add(report)
        
        assert result.id > 0
        assert result.user_id == 100
        assert result.start_location_id == 200
        assert result.obstruction_type == "road_closure"
        assert result.resolved is False
    
    def test_add_technical_report(self, test_db_session):
        """Test adding a technical report"""
        repo = SqlReportRepo(test_db_session)
        
        report = TechnicalReport(
            id=0,
            user_id=100,
            description="App crashes when viewing saved routes"
        )
        
        result = repo.add(report)
        
        assert result.id > 0
        assert result.user_id == 100
        assert result.description == "App crashes when viewing saved routes"
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving report by ID"""
        repo = SqlReportRepo(test_db_session)
        
        # Add a report
        report = IncidentReport(
            id=0,
            user_id=100,
            obstruction_type="pothole",
            description="Large pothole on main road"
        )
        added = repo.add(report)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert isinstance(found, IncidentReport)
        assert found.obstruction_type == "pothole"
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent report"""
        repo = SqlReportRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_list_reports(self, test_db_session):
        """Test listing all reports"""
        repo = SqlReportRepo(test_db_session)
        
        # Add multiple reports
        report1 = IncidentReport(id=0, user_id=100, obstruction_type="accident", description="Accident")
        report2 = TechnicalReport(id=0, user_id=101, description="Bug report")
        
        repo.add(report1)
        repo.add(report2)
        
        # List all
        reports = repo.list()
        
        assert len(reports) >= 2
    
    def test_list_by_user(self, test_db_session):
        """Test listing reports by specific user"""
        repo = SqlReportRepo(test_db_session)
        
        # Add reports for different users
        report1 = IncidentReport(id=0, user_id=100, obstruction_type="accident", description="Accident 1")
        report2 = IncidentReport(id=0, user_id=100, obstruction_type="pothole", description="Pothole")
        report3 = TechnicalReport(id=0, user_id=200, description="Bug")
        
        repo.add(report1)
        repo.add(report2)
        repo.add(report3)
        
        # Get reports for user 100
        user_reports = repo.list_by_user(100)
        
        assert len(user_reports) == 2
        assert all(r.user_id == 100 for r in user_reports)
    
    def test_list_incident_reports(self, test_db_session):
        """Test listing only incident reports"""
        repo = SqlReportRepo(test_db_session)
        
        # Add different types of reports
        report1 = IncidentReport(id=0, user_id=100, obstruction_type="accident", description="Accident")
        report2 = TechnicalReport(id=0, user_id=101, description="Bug")
        report3 = IncidentReport(id=0, user_id=102, obstruction_type="pothole", description="Pothole")
        
        repo.add(report1)
        repo.add(report2)
        repo.add(report3)
        
        # Get only incident reports
        incident_reports = repo.list_incident_reports()
        
        assert len(incident_reports) == 2
        assert all(isinstance(r, IncidentReport) for r in incident_reports)
    
    def test_update_incident_report(self, test_db_session):
        """Test updating an incident report"""
        repo = SqlReportRepo(test_db_session)
        
        # Add a report
        report = IncidentReport(
            id=0,
            user_id=100,
            obstruction_type="accident",
            description="Accident on highway",
            resolved=False
        )
        added = repo.add(report)
        
        # Update it
        added.resolved = True
        added.description = "Accident cleared"
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert isinstance(updated, IncidentReport)
        assert updated.resolved is True
        assert updated.description == "Accident cleared"
    
    def test_update_technical_report(self, test_db_session):
        """Test updating a technical report"""
        repo = SqlReportRepo(test_db_session)
        
        # Add a report
        report = TechnicalReport(
            id=0,
            user_id=100,
            description="Login issue"
        )
        added = repo.add(report)
        
        # Update it
        added.description = "Login issue - fixed in v2.0"
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert isinstance(updated, TechnicalReport)
        assert updated.description == "Login issue - fixed in v2.0"
    
    def test_delete_report(self, test_db_session):
        """Test deleting a report"""
        repo = SqlReportRepo(test_db_session)
        
        # Add a report
        report = IncidentReport(
            id=0,
            user_id=100,
            obstruction_type="accident",
            description="Test"
        )
        added = repo.add(report)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_report(self, test_db_session):
        """Test deleting non-existent report"""
        repo = SqlReportRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
