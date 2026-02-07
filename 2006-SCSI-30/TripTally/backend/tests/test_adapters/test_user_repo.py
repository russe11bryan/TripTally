"""
Tests for User repository adapter.
Uses SQLite in-memory database for testing.
"""
import pytest
from app.models.account import User
from app.adapters.sqlalchemy_user_repo import SqlUserRepo


class TestSqlUserRepo:
    """Test SqlUserRepo adapter with in-memory database."""
    
    def test_add_user(self, test_db_session):
        """Test adding a user to the database."""
        repo = SqlUserRepo(test_db_session)
        
        user = User(
            id=0,  # Will be set by database
            email="newuser@example.com",
            password="hashed_password",
            contact_number="+65 1234 5678",
            display_name="New User"
        )
        
        saved_user = repo.add(user)
        
        # Verify user was saved and ID was assigned
        assert saved_user.id > 0
        assert saved_user.email == "newuser@example.com"
        assert saved_user.display_name == "New User"
    
    def test_get_by_id(self, test_db_session):
        """Test retrieving user by ID."""
        repo = SqlUserRepo(test_db_session)
        
        # Create and save a user
        user = User(
            id=0,
            email="test@example.com",
            password="pass",
            contact_number="+65 1234 5678",
            display_name="Test User"
        )
        saved_user = repo.add(user)
        
        # Retrieve by ID
        retrieved = repo.get_by_id(saved_user.id)
        
        assert retrieved is not None
        assert retrieved.id == saved_user.id
        assert retrieved.email == "test@example.com"
        assert retrieved.display_name == "Test User"
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test retrieving non-existent user returns None."""
        repo = SqlUserRepo(test_db_session)
        
        user = repo.get_by_id(9999)
        
        assert user is None
    
    def test_get_by_email(self, test_db_session):
        """Test retrieving user by email."""
        repo = SqlUserRepo(test_db_session)
        
        user = User(
            id=0,
            email="unique@example.com",
            password="pass",
            contact_number="+65 1234 5678"
        )
        repo.add(user)
        
        retrieved = repo.get_by_email("unique@example.com")
        
        assert retrieved is not None
        assert retrieved.email == "unique@example.com"
    
    def test_get_by_email_not_found(self, test_db_session):
        """Test retrieving non-existent email returns None."""
        repo = SqlUserRepo(test_db_session)
        
        user = repo.get_by_email("nonexistent@example.com")
        
        assert user is None
    
    def test_list_users(self, test_db_session):
        """Test listing all users."""
        repo = SqlUserRepo(test_db_session)
        
        # Add multiple users
        for i in range(3):
            user = User(
                id=0,
                email=f"user{i}@example.com",
                password="pass",
                contact_number="+65 1234 5678",
                display_name=f"User {i}"
            )
            repo.add(user)
        
        users = repo.list()
        
        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)
    
    def test_list_empty(self, test_db_session):
        """Test listing users when database is empty."""
        repo = SqlUserRepo(test_db_session)
        
        users = repo.list()
        
        assert users == []
    
    def test_update_user(self, test_db_session):
        """Test updating a user."""
        repo = SqlUserRepo(test_db_session)
        
        # Create user
        user = User(
            id=0,
            email="update@example.com",
            password="pass",
            contact_number="+65 1234 5678",
            display_name="Original Name"
        )
        saved = repo.add(user)
        
        # Update user
        saved.display_name = "Updated Name"
        saved.saved_locations = [1, 2, 3]
        updated = repo.update(saved)
        
        # Verify update persisted
        retrieved = repo.get_by_id(saved.id)
        assert retrieved.display_name == "Updated Name"
        assert retrieved.saved_locations == [1, 2, 3]
    
    def test_delete_user(self, test_db_session):
        """Test deleting a user."""
        repo = SqlUserRepo(test_db_session)
        
        user = User(
            id=0,
            email="delete@example.com",
            password="pass",
            contact_number="+65 1234 5678"
        )
        saved = repo.add(user)
        user_id = saved.id
        
        # Delete user
        result = repo.delete(user_id)
        assert result is True
        
        # Verify user was deleted
        retrieved = repo.get_by_id(user_id)
        assert retrieved is None
    
    def test_delete_nonexistent_user(self, test_db_session):
        """Test deleting non-existent user returns False."""
        repo = SqlUserRepo(test_db_session)
        
        result = repo.delete(9999)
        assert result is False
    
    def test_saved_locations_persistence(self, test_db_session):
        """Test that saved_locations list is persisted correctly."""
        repo = SqlUserRepo(test_db_session)
        
        user = User(
            id=0,
            email="locations@example.com",
            password="pass",
            contact_number="+65 1234 5678",
            saved_locations=[10, 20, 30, 40]
        )
        saved = repo.add(user)
        
        # Retrieve and verify list
        retrieved = repo.get_by_id(saved.id)
        assert retrieved.saved_locations == [10, 20, 30, 40]
    
    def test_empty_saved_locations(self, test_db_session):
        """Test user with empty saved_locations."""
        repo = SqlUserRepo(test_db_session)
        
        user = User(
            id=0,
            email="empty@example.com",
            password="pass",
            contact_number="+65 1234 5678",
            saved_locations=[]
        )
        saved = repo.add(user)
        
        retrieved = repo.get_by_id(saved.id)
        assert retrieved.saved_locations == []
