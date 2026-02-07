"""
Integration tests for user creation API with password validation
Tests actual HTTP responses with expected vs actual outputs
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.models.account import User

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user_validation.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestUserCreationSuccess:
    """Test successful user creation scenarios - Expected: 201 Created"""
    
    def test_valid_user_creation(self):
        """
        Test Case: Valid user creation with strong password
        Expected Output: 201 Created
        Expected Response: User object with id, email, username, display_name
        """
        payload = {
            "email": "john.doe@example.com",
            "username": "johndoe",
            "password": "SecurePass123!",
            "display_name": "John Doe"
        }
        
        response = client.post("/users", json=payload)
        
        # Expected Output
        expected_status = 201
        expected_keys = ["id", "email", "username", "display_name"]
        
        # Actual Output
        actual_status = response.status_code
        actual_data = response.json()
        
        print("\n" + "="*70)
        print("TEST: Valid User Creation")
        print("="*70)
        print(f"Request Payload: {payload}")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Response Keys: {expected_keys}")
        print(f"Actual Response Keys:   {list(actual_data.keys())}")
        print(f"\nActual Response Data:")
        print(f"  ID:           {actual_data.get('id')}")
        print(f"  Email:        {actual_data.get('email')}")
        print(f"  Username:     {actual_data.get('username')}")
        print(f"  Display Name: {actual_data.get('display_name')}")
        print("="*70)
        
        # Assertions
        assert actual_status == expected_status
        assert all(key in actual_data for key in expected_keys)
        assert actual_data["email"] == payload["email"]
        assert actual_data["username"] == payload["username"]
        assert actual_data["display_name"] == payload["display_name"]
        assert "password" not in actual_data  # Password should never be returned


class TestPasswordValidationErrors:
    """Test password validation failures - Expected: 400 Bad Request"""
    
    def test_password_too_short(self):
        """
        Test Case: Password less than 8 characters
        Expected Output: 400 Bad Request
        Expected Error: "Password must be at least 8 characters long"
        """
        payload = {
            "email": "user@example.com",
            "username": "testuser",
            "password": "Short1!",  # Only 7 characters
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        # Expected Output
        expected_status = 400
        expected_error = "Password must be at least 8 characters long"
        
        # Actual Output
        actual_status = response.status_code
        actual_data = response.json()
        actual_error = actual_data.get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Password Too Short")
        print("="*70)
        print(f"Password Provided: '{payload['password']}' (length: {len(payload['password'])})")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error
    
    def test_password_no_numbers(self):
        """
        Test Case: Password without numbers
        Expected Output: 400 Bad Request
        Expected Error: "Password must contain at least one number"
        """
        payload = {
            "email": "user@example.com",
            "username": "testuser",
            "password": "NoNumbers!",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        expected_status = 400
        expected_error = "Password must contain at least one number"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Password Without Numbers")
        print("="*70)
        print(f"Password Provided: '{payload['password']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error
    
    def test_password_no_letters(self):
        """
        Test Case: Password without letters
        Expected Output: 400 Bad Request
        Expected Error: "Password must contain at least one letter"
        """
        payload = {
            "email": "user@example.com",
            "username": "testuser",
            "password": "12345678!",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        expected_status = 400
        expected_error = "Password must contain at least one letter"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Password Without Letters")
        print("="*70)
        print(f"Password Provided: '{payload['password']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error
    
    def test_password_no_special_char(self):
        """
        Test Case: Password without special characters
        Expected Output: 400 Bad Request
        Expected Error: "Password must contain at least one special character"
        """
        payload = {
            "email": "user@example.com",
            "username": "testuser",
            "password": "Password123",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        expected_status = 400
        expected_error = "Password must contain at least one special character"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Password Without Special Character")
        print("="*70)
        print(f"Password Provided: '{payload['password']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error
    
    def test_password_with_whitespace(self):
        """
        Test Case: Password with whitespace
        Expected Output: 400 Bad Request
        Expected Error: "Password cannot contain whitespace"
        """
        payload = {
            "email": "user@example.com",
            "username": "testuser",
            "password": "Pass word123!",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        expected_status = 400
        expected_error = "Password cannot contain whitespace"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Password With Whitespace")
        print("="*70)
        print(f"Password Provided: '{payload['password']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error


class TestEmailValidationErrors:
    """Test email validation failures - Expected: 400 Bad Request"""
    
    def test_invalid_email_format(self):
        """
        Test Case: Invalid email format
        Expected Output: 400 Bad Request
        Expected Error: "Invalid email format"
        """
        payload = {
            "email": "notanemail",
            "username": "testuser",
            "password": "ValidPass123!",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        # Pydantic validation returns 422 for invalid email format
        expected_status = 422
        expected_error = "email address"
        actual_status = response.status_code
        actual_error = str(response.json().get("detail", ""))
        
        print("\n" + "="*70)
        print("TEST: Invalid Email Format")
        print("="*70)
        print(f"Email Provided: '{payload['email']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error Contains: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error.lower()
    
    def test_email_missing_domain(self):
        """
        Test Case: Email missing domain
        Expected Output: 400 Bad Request
        Expected Error: "Invalid email format"
        """
        payload = {
            "email": "user@",
            "username": "testuser",
            "password": "ValidPass123!",
            "display_name": "Test User"
        }
        
        response = client.post("/users", json=payload)
        
        # Pydantic validation returns 422 for invalid email format
        expected_status = 422
        expected_error = "@-sign"
        actual_status = response.status_code
        actual_error = str(response.json().get("detail", ""))
        
        print("\n" + "="*70)
        print("TEST: Email Missing Domain")
        print("="*70)
        print(f"Email Provided: '{payload['email']}'")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error Contains: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error


class TestDuplicateAccountErrors:
    """Test duplicate account prevention - Expected: 400 Bad Request"""
    
    def test_duplicate_email(self):
        """
        Test Case: Duplicate email address
        Expected Output: 400 Bad Request
        Expected Error: "Email already registered"
        """
        # First, create a user
        payload1 = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "ValidPass123!",
            "display_name": "User One"
        }
        response1 = client.post("/users", json=payload1)
        
        # Try to create another user with same email
        payload2 = {
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "DifferentPass456!",
            "display_name": "User Two"
        }
        response2 = client.post("/users", json=payload2)
        
        expected_status_first = 201
        expected_status_second = 400
        expected_error = "Email already registered"
        
        actual_status_first = response1.status_code
        actual_status_second = response2.status_code
        actual_error = response2.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Duplicate Email Address")
        print("="*70)
        print("First User Creation:")
        print(f"  Email: {payload1['email']}")
        print(f"  Expected Status: {expected_status_first}")
        print(f"  Actual Status:   {actual_status_first}")
        print(f"\nSecond User Creation (Same Email):")
        print(f"  Email: {payload2['email']}")
        print(f"  Expected Status: {expected_status_second}")
        print(f"  Actual Status:   {actual_status_second}")
        print(f"\n  Expected Error: '{expected_error}'")
        print(f"  Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status_first == expected_status_first
        assert actual_status_second == expected_status_second
        assert expected_error in actual_error
    
    def test_duplicate_username(self):
        """
        Test Case: Duplicate username
        Expected Output: 400 Bad Request
        Expected Error: "Username already taken"
        """
        # First, create a user
        payload1 = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "password": "ValidPass123!",
            "display_name": "User One"
        }
        response1 = client.post("/users", json=payload1)
        
        # Try to create another user with same username
        payload2 = {
            "email": "user2@example.com",
            "username": "duplicateuser",
            "password": "DifferentPass456!",
            "display_name": "User Two"
        }
        response2 = client.post("/users", json=payload2)
        
        expected_status_first = 201
        expected_status_second = 400
        expected_error = "Username already taken"
        
        actual_status_first = response1.status_code
        actual_status_second = response2.status_code
        actual_error = response2.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Duplicate Username")
        print("="*70)
        print("First User Creation:")
        print(f"  Username: {payload1['username']}")
        print(f"  Expected Status: {expected_status_first}")
        print(f"  Actual Status:   {actual_status_first}")
        print(f"\nSecond User Creation (Same Username):")
        print(f"  Username: {payload2['username']}")
        print(f"  Expected Status: {expected_status_second}")
        print(f"  Actual Status:   {actual_status_second}")
        print(f"\n  Expected Error: '{expected_error}'")
        print(f"  Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status_first == expected_status_first
        assert actual_status_second == expected_status_second
        assert expected_error in actual_error


class TestAuthenticationErrors:
    """Test authentication failures - Expected: 401 Unauthorized"""
    
    def test_login_invalid_credentials(self):
        """
        Test Case: Login with invalid credentials
        Expected Output: 401 Unauthorized
        Expected Error: "Invalid credentials"
        """
        # First, create a user
        payload_create = {
            "email": "authtest@example.com",
            "username": "authuser",
            "password": "CorrectPass123!",
            "display_name": "Auth User"
        }
        client.post("/users", json=payload_create)
        
        # Try to login with wrong password
        payload_login = {
            "identifier": "authtest@example.com",
            "password": "WrongPassword123!"
        }
        response = client.post("/auth/login", json=payload_login)
        
        expected_status = 401
        expected_error = "Invalid credentials"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Login With Invalid Credentials")
        print("="*70)
        print(f"User Created: {payload_create['email']}")
        print(f"Correct Password: {payload_create['password']}")
        print(f"\nLogin Attempt:")
        print(f"  Email: {payload_login['identifier']}")
        print(f"  Password: {payload_login['password']}")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error
    
    def test_login_nonexistent_user(self):
        """
        Test Case: Login with non-existent user
        Expected Output: 401 Unauthorized
        Expected Error: "Invalid credentials"
        """
        payload_login = {
            "identifier": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = client.post("/auth/login", json=payload_login)
        
        expected_status = 401
        expected_error = "Invalid credentials"
        actual_status = response.status_code
        actual_error = response.json().get("detail", "")
        
        print("\n" + "="*70)
        print("TEST: Login With Non-existent User")
        print("="*70)
        print(f"Email: {payload_login['identifier']}")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Error: '{expected_error}'")
        print(f"Actual Error:   '{actual_error}'")
        print("="*70)
        
        assert actual_status == expected_status
        assert expected_error in actual_error


class TestSuccessfulAuthentication:
    """Test successful authentication - Expected: 200 OK"""
    
    def test_login_success(self):
        """
        Test Case: Successful login
        Expected Output: 200 OK
        Expected Response: Access token and token type
        """
        # First, create a user
        payload_create = {
            "email": "logintest@example.com",
            "username": "loginuser",
            "password": "CorrectPass123!",
            "display_name": "Login User"
        }
        client.post("/users", json=payload_create)
        
        # Login with correct credentials
        payload_login = {
            "identifier": "logintest@example.com",
            "password": "CorrectPass123!"
        }
        response = client.post("/auth/login", json=payload_login)
        
        expected_status = 200
        expected_keys = ["access_token", "token_type"]
        expected_token_type = "bearer"
        
        actual_status = response.status_code
        actual_data = response.json()
        actual_token_type = actual_data.get("token_type", "")
        
        print("\n" + "="*70)
        print("TEST: Successful Login")
        print("="*70)
        print(f"User: {payload_login['identifier']}")
        print(f"\nExpected Status Code: {expected_status}")
        print(f"Actual Status Code:   {actual_status}")
        print(f"\nExpected Response Keys: {expected_keys}")
        print(f"Actual Response Keys:   {list(actual_data.keys())}")
        print(f"\nExpected Token Type: '{expected_token_type}'")
        print(f"Actual Token Type:   '{actual_token_type}'")
        print(f"\nAccess Token Present: {'access_token' in actual_data}")
        print(f"Token Length: {len(actual_data.get('access_token', ''))} characters")
        print("="*70)
        
        assert actual_status == expected_status
        assert all(key in actual_data for key in expected_keys)
        assert actual_token_type == expected_token_type
        assert len(actual_data.get("access_token", "")) > 0
