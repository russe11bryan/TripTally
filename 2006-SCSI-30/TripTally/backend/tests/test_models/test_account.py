"""
Tests for Account domain models (User, Admin).
No database needed - pure Python dataclass testing.
"""
import pytest
from app.models.account import Account, User, Admin


class TestAccount:
    """Test Account base model."""
    
    def test_create_account(self):
        """Test creating an Account instance."""
        account = Account(
            id=1,
            email="test@example.com",
            password="password123",
            contact_number="+65 1234 5678",
            status="active"
        )
        
        assert account.id == 1
        assert account.email == "test@example.com"
        assert account.password == "password123"
        assert account.contact_number == "+65 1234 5678"
        assert account.status == "active"
        assert account.type == "account"
    
    def test_account_defaults(self):
        """Test Account default values."""
        account = Account(
            id=1,
            email="test@example.com",
            password="pass",
            contact_number="+65 1234 5678"
        )
        
        assert account.status == "active"
        assert account.type == "account"


class TestUser:
    """Test User model."""
    
    def test_create_user(self):
        """Test creating a User instance."""
        user = User(
            id=1,
            email="user@example.com",
            password="password123",
            contact_number="+65 1234 5678",
            display_name="John Doe"
        )
        
        assert user.id == 1
        assert user.email == "user@example.com"
        assert user.display_name == "John Doe"
        assert user.type == "user"
        assert user.saved_locations == []
    
    def test_user_saved_locations(self):
        """Test User with saved locations."""
        user = User(
            id=1,
            email="user@example.com",
            password="pass",
            contact_number="+65 1234 5678",
            saved_locations=[1, 2, 3, 4]
        )
        
        assert len(user.saved_locations) == 4
        assert 1 in user.saved_locations
        assert 4 in user.saved_locations
    
    def test_user_defaults(self):
        """Test User default values."""
        user = User(
            id=1,
            email="user@example.com",
            password="pass",
            contact_number="+65 1234 5678"
        )
        
        assert user.display_name == ""
        assert user.saved_locations == []
        assert user.status == "active"
        assert user.type == "user"


class TestAdmin:
    """Test Admin model."""
    
    def test_create_admin(self):
        """Test creating an Admin instance."""
        admin = Admin(
            id=1,
            email="admin@example.com",
            password="admin_password",
            contact_number="+65 9999 9999"
        )
        
        assert admin.id == 1
        assert admin.email == "admin@example.com"
        assert admin.type == "admin"
        assert admin.status == "active"
    
    def test_admin_defaults(self):
        """Test Admin default values."""
        admin = Admin(
            id=1,
            email="admin@example.com",
            password="pass",
            contact_number="+65 1111 1111"
        )
        
        assert admin.status == "active"
        assert admin.type == "admin"
