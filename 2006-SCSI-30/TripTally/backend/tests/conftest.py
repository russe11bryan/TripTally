"""
Pytest configuration and shared fixtures.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set required environment variables for testing BEFORE importing app modules
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "test_api_key_for_testing")
os.environ.setdefault("GOOGLE_SERVER_API_KEY", "test_api_key_for_testing")
os.environ.setdefault("REQUEST_TIMEOUT", "10")
os.environ.setdefault("CACHE_TTL_SECONDS", "300")

from app.core.db import Base
from fastapi.testclient import TestClient
from app.core.db import Base, get_db
from app.adapters import tables  # Import all table definitions
from app.main import app


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create an in-memory SQLite database engine for testing.
    Each test gets a fresh database.
    """
    # Use SQLite in-memory database (fast, isolated)
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup: drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create a database session for testing.
    Automatically rolls back after each test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup: rollback and close
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """
    Create a FastAPI TestClient with overridden database dependency.
    This client can be used to make requests to the API endpoints.
    """
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass  # Session cleanup is handled by test_db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup: clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "password": "hashed_password_123",
        "contact_number": "+65 1234 5678",
        "status": "active",
        "display_name": "Test User",
        "saved_locations": [1, 2, 3]
    }


@pytest.fixture
def sample_location_data():
    """Sample location data for testing."""
    return {
        "id": 1,
        "name": "NTU Main Gate",
        "lat": 1.3483,
        "lng": 103.6831
    }


@pytest.fixture
def sample_route_data():
    """Sample route data for testing."""
    return {
        "id": 1,
        "start_location_id": 1,
        "end_location_id": 2,
        "subtype": "recommended",
        "transport_mode": "driving",
        "route_line": [1, 3, 5, 2],
        "metrics_id": None
    }
