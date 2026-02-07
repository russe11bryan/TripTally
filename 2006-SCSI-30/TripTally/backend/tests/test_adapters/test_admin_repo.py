"""
Integration tests for SqlAdminRepo adapter.
Tests the SQLAlchemy implementation of AdminRepository.
"""
import pytest
from app.models.account import Admin
from app.adapters.sqlalchemy_admin_repo import SqlAdminRepo


class TestSqlAdminRepo:
    """Tests for SqlAdminRepo adapter"""
    
    def test_add_admin(self, test_db_session):
        """Test adding a new admin"""
        repo = SqlAdminRepo(test_db_session)
        
        admin = Admin(
            id=0,
            email="admin@triptally.com",
            password="hashed_password_123",
            contact_number="+65 1234 5678",
            status="active"
        )
        
        result = repo.add(admin)
        
        assert result.id > 0
        assert result.email == "admin@triptally.com"
        assert result.password == "hashed_password_123"
        assert result.contact_number == "+65 1234 5678"
        assert result.status == "active"
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving admin by ID"""
        repo = SqlAdminRepo(test_db_session)
        
        # Add an admin
        admin = Admin(
            id=0,
            email="admin1@triptally.com",
            password="hashed_pass",
            contact_number="+65 9876 5432",
            status="active"
        )
        added = repo.add(admin)
        
        # Retrieve it
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.email == "admin1@triptally.com"
        assert found.contact_number == "+65 9876 5432"
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent admin"""
        repo = SqlAdminRepo(test_db_session)
        
        result = repo.get_by_id(99999)
        
        assert result is None
    
    def test_get_by_email(self, test_db_session):
        """Test retrieving admin by email"""
        repo = SqlAdminRepo(test_db_session)
        
        # Add an admin
        admin = Admin(
            id=0,
            email="unique.admin@triptally.com",
            password="secure_hash",
            contact_number="+65 1111 2222"
        )
        repo.add(admin)
        
        # Retrieve by email
        found = repo.get_by_email("unique.admin@triptally.com")
        
        assert found is not None
        assert found.email == "unique.admin@triptally.com"
        assert found.password == "secure_hash"
    
    def test_get_by_email_not_found(self, test_db_session):
        """Test retrieving admin by non-existent email"""
        repo = SqlAdminRepo(test_db_session)
        
        result = repo.get_by_email("nonexistent@triptally.com")
        
        assert result is None
    
    def test_list_admins(self, test_db_session):
        """Test listing all admins"""
        repo = SqlAdminRepo(test_db_session)
        
        # Add multiple admins
        admin1 = Admin(id=0, email="admin1@triptally.com", password="pass1", contact_number="+65 1111")
        admin2 = Admin(id=0, email="admin2@triptally.com", password="pass2", contact_number="+65 2222")
        
        repo.add(admin1)
        repo.add(admin2)
        
        # List all
        admins = repo.list()
        
        assert len(admins) >= 2
    
    def test_list_empty(self, test_db_session):
        """Test listing when no admins exist"""
        repo = SqlAdminRepo(test_db_session)
        
        admins = repo.list()
        
        assert admins == []
    
    def test_update_admin(self, test_db_session):
        """Test updating an admin"""
        repo = SqlAdminRepo(test_db_session)
        
        # Add an admin
        admin = Admin(
            id=0,
            email="admin@triptally.com",
            password="old_password",
            contact_number="+65 1234 5678",
            status="active"
        )
        added = repo.add(admin)
        
        # Update it
        added.password = "new_password_hash"
        added.contact_number = "+65 8765 4321"
        added.status = "inactive"
        repo.update(added)
        
        # Verify update
        updated = repo.get_by_id(added.id)
        assert updated.password == "new_password_hash"
        assert updated.contact_number == "+65 8765 4321"
        assert updated.status == "inactive"
    
    def test_delete_admin(self, test_db_session):
        """Test deleting an admin"""
        repo = SqlAdminRepo(test_db_session)
        
        # Add an admin
        admin = Admin(
            id=0,
            email="temp.admin@triptally.com",
            password="temp_pass",
            contact_number="+65 9999 9999"
        )
        added = repo.add(admin)
        
        # Delete it
        result = repo.delete(added.id)
        assert result is True
        
        # Verify deletion
        found = repo.get_by_id(added.id)
        assert found is None
    
    def test_delete_nonexistent_admin(self, test_db_session):
        """Test deleting non-existent admin"""
        repo = SqlAdminRepo(test_db_session)
        
        result = repo.delete(99999)
        
        assert result is False
    
    def test_admin_defaults(self, test_db_session):
        """Test admin with default values"""
        repo = SqlAdminRepo(test_db_session)
        
        admin = Admin(
            id=0,
            email="minimal@triptally.com",
            password="minimal_pass"
        )
        
        added = repo.add(admin)
        found = repo.get_by_id(added.id)
        
        assert found.contact_number == ""
        assert found.status == "active"
    
    def test_multiple_admins_unique_emails(self, test_db_session):
        """Test that multiple admins can be added with different emails"""
        repo = SqlAdminRepo(test_db_session)
        
        admin1 = Admin(id=0, email="admin1@triptally.com", password="pass1", contact_number="+65 1111")
        admin2 = Admin(id=0, email="admin2@triptally.com", password="pass2", contact_number="+65 2222")
        admin3 = Admin(id=0, email="admin3@triptally.com", password="pass3", contact_number="+65 3333")
        
        added1 = repo.add(admin1)
        added2 = repo.add(admin2)
        added3 = repo.add(admin3)
        
        assert added1.id != added2.id != added3.id
        
        # Verify all can be retrieved
        assert repo.get_by_email("admin1@triptally.com") is not None
        assert repo.get_by_email("admin2@triptally.com") is not None
        assert repo.get_by_email("admin3@triptally.com") is not None
