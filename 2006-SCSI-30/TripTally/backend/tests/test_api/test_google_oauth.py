"""
Tests for Google OAuth authentication endpoint.
Tests both valid and invalid token scenarios.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from app.models.account import User


class TestGoogleOAuthValidInputs:
    """Test Google OAuth with valid inputs - new and existing users."""
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_new_user_success(self, mock_verify, client, test_db_session):
        """
        Test successful Google authentication for a NEW user.
        Should create account and return access token.
        """
        # Mock Google token verification response for new user
        mock_verify.return_value = {
            'sub': 'google123456',  # Google user ID
            'email': 'newuser@gmail.com',
            'name': 'New User',
            'email_verified': True,
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        # Make request
        response = client.post(
            "/auth/google",
            json={"id_token": "valid_google_token_for_new_user"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        
        # Verify user was created in database
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        repo = SqlUserRepo(test_db_session)
        user = repo.get_by_email('newuser@gmail.com')
        assert user is not None
        assert user.email == 'newuser@gmail.com'
        assert user.display_name == 'New User'
        assert user.google_id == 'google123456'
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_existing_user_success(self, mock_verify, client, test_db_session):
        """
        Test successful Google authentication for an EXISTING user.
        Should return access token without creating duplicate.
        """
        # Pre-create user in database
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        from app.models.account import User
        
        repo = SqlUserRepo(test_db_session)
        existing_user = User(
            id=0,
            email='existinguser@gmail.com',
            display_name='Existing User',
            google_id='google789012',
            password_hash=None,
            created_at=datetime.utcnow()
        )
        repo.add(existing_user)
        
        # Mock Google token verification for existing user
        mock_verify.return_value = {
            'sub': 'google789012',  # Same Google ID as existing user
            'email': 'existinguser@gmail.com',
            'name': 'Existing User',
            'email_verified': True,
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        # Make request
        response = client.post(
            "/auth/google",
            json={"id_token": "valid_google_token_for_existing_user"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        
        # Verify no duplicate user was created
        users = test_db_session.query(repo._table).filter_by(email='existinguser@gmail.com').all()
        assert len(users) == 1  # Only one user with this email
        assert users[0].google_id == 'google789012'
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_with_minimal_user_info(self, mock_verify, client, test_db_session):
        """
        Test Google auth with minimal user info (only email, no name).
        Should use email prefix as display name.
        """
        mock_verify.return_value = {
            'sub': 'google_minimal_123',
            'email': 'minimal@gmail.com',
            # No 'name' field
            'email_verified': True,
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "valid_token_minimal_info"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        # Check user was created with email prefix as name
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        repo = SqlUserRepo(test_db_session)
        user = repo.get_by_email('minimal@gmail.com')
        assert user is not None
        assert user.display_name == 'minimal'  # Email prefix
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_with_special_characters_in_name(self, mock_verify, client, test_db_session):
        """
        Test Google auth with special characters in user name.
        Should handle unicode and special characters properly.
        """
        mock_verify.return_value = {
            'sub': 'google_special_456',
            'email': 'user@gmail.com',
            'name': 'José García 李明',  # Spanish and Chinese characters
            'email_verified': True,
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "valid_token_special_chars"}
        )
        
        assert response.status_code == 200
        
        # Verify special characters are preserved
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        repo = SqlUserRepo(test_db_session)
        user = repo.get_by_email('user@gmail.com')
        assert user is not None
        assert user.display_name == 'José García 李明'


class TestGoogleOAuthInvalidInputs:
    """Test Google OAuth with invalid inputs and error cases."""
    
    def test_google_auth_empty_token(self, client):
        """Test with empty string token - should return 401."""
        response = client.post(
            "/auth/google",
            json={"id_token": ""}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid Google token" in data["detail"]
    
    def test_google_auth_malformed_token(self, client):
        """Test with malformed token (not JWT format) - should return 401."""
        response = client.post(
            "/auth/google",
            json={"id_token": "not-a-valid-jwt-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_google_auth_missing_token_field(self, client):
        """Test with missing id_token field - should return 422 (validation error)."""
        response = client.post(
            "/auth/google",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Pydantic validation error
        assert any('id_token' in str(error) for error in data["detail"])
    
    def test_google_auth_null_token(self, client):
        """Test with null token - should return 422 (validation error)."""
        response = client.post(
            "/auth/google",
            json={"id_token": None}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_expired_token(self, mock_verify, client):
        """Test with expired token - should return 401."""
        # Simulate expired token error
        mock_verify.side_effect = ValueError("Token expired")
        
        response = client.post(
            "/auth/google",
            json={"id_token": "expired_google_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid Google token" in data["detail"]
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_wrong_client_id(self, mock_verify, client):
        """Test with token from different client ID - should return 401."""
        # Mock token with wrong audience/client_id
        mock_verify.return_value = {
            'sub': 'google123',
            'email': 'user@gmail.com',
            'iss': 'https://accounts.google.com',
            'aud': 'wrong-client-id'  # Different from configured client ID
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_with_wrong_client_id"}
        )
        
        assert response.status_code == 401
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_invalid_signature(self, mock_verify, client):
        """Test with token with invalid signature - should return 401."""
        # Simulate invalid signature error
        mock_verify.side_effect = ValueError("Invalid token signature")
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_with_invalid_signature"}
        )
        
        assert response.status_code == 401
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_missing_required_fields(self, mock_verify, client):
        """Test with token missing required fields (sub or email) - should return 400."""
        # Mock token without 'sub' field
        mock_verify.return_value = {
            'email': 'user@gmail.com',
            'name': 'User',
            # Missing 'sub' field
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_missing_sub"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Missing required Google user information" in data["detail"]
    
    def test_google_auth_sql_injection_attempt(self, client):
        """Test with SQL injection attempt in token - should be safely rejected."""
        malicious_token = "'; DROP TABLE users;--"
        
        response = client.post(
            "/auth/google",
            json={"id_token": malicious_token}
        )
        
        assert response.status_code == 401
        # Should not cause any database errors
    
    def test_google_auth_very_long_token(self, client):
        """Test with extremely long invalid token - should handle gracefully."""
        long_token = "a" * 10000  # 10,000 characters
        
        response = client.post(
            "/auth/google",
            json={"id_token": long_token}
        )
        
        assert response.status_code == 401
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_invalid_issuer(self, mock_verify, client):
        """Test with token from invalid issuer - should return 401."""
        mock_verify.return_value = {
            'sub': 'user123',
            'email': 'user@gmail.com',
            'iss': 'https://malicious-site.com',  # Invalid issuer
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_invalid_issuer"}
        )
        
        assert response.status_code == 401


class TestGoogleOAuthEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_email_case_sensitivity(self, mock_verify, client, test_db_session):
        """Test that emails are handled case-insensitively."""
        # Create user with lowercase email
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        from app.models.account import User
        
        repo = SqlUserRepo(test_db_session)
        user = User(
            id=0,
            email='testuser@gmail.com',  # lowercase
            display_name='Test User',
            google_id='google_case_test',
            password_hash=None,
            created_at=datetime.utcnow()
        )
        repo.add(user)
        
        # Token with uppercase email
        mock_verify.return_value = {
            'sub': 'google_case_test',
            'email': 'TESTUSER@GMAIL.COM',  # UPPERCASE
            'name': 'Test User',
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_uppercase_email"}
        )
        
        # Should successfully authenticate existing user
        assert response.status_code == 200
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_max_length_email(self, mock_verify, client):
        """Test with maximum length email address."""
        # RFC 5321: max 64 chars before @, 255 chars total
        long_email = "a" * 64 + "@" + "b" * 60 + ".com"
        
        mock_verify.return_value = {
            'sub': 'google_long_email',
            'email': long_email,
            'name': 'Long Email User',
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        response = client.post(
            "/auth/google",
            json={"id_token": "token_long_email"}
        )
        
        assert response.status_code == 200
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_google_auth_concurrent_requests(self, mock_verify, client, test_db_session):
        """Test handling of concurrent requests for same new user."""
        mock_verify.return_value = {
            'sub': 'google_concurrent',
            'email': 'concurrent@gmail.com',
            'name': 'Concurrent User',
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        # Make multiple concurrent-like requests
        response1 = client.post(
            "/auth/google",
            json={"id_token": "token_concurrent_1"}
        )
        response2 = client.post(
            "/auth/google",
            json={"id_token": "token_concurrent_2"}
        )
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Should not create duplicate users
        from app.adapters.sqlalchemy_user_repo import SqlUserRepo
        repo = SqlUserRepo(test_db_session)
        users = test_db_session.query(repo._table).filter_by(email='concurrent@gmail.com').all()
        assert len(users) <= 1  # Should handle race condition


class TestGoogleOAuthIntegration:
    """Integration tests for Google OAuth flow."""
    
    @patch('app.services.google_oauth_service.id_token.verify_oauth2_token')
    def test_full_google_oauth_flow_new_user(self, mock_verify, client, test_db_session):
        """
        Test complete OAuth flow for new user:
        1. User signs in with Google
        2. Backend verifies token
        3. Creates new user
        4. Returns JWT token
        5. User can access protected endpoints
        """
        # Step 1-2: Mock Google token verification
        mock_verify.return_value = {
            'sub': 'google_integration_test',
            'email': 'integration@gmail.com',
            'name': 'Integration Test User',
            'iss': 'https://accounts.google.com',
            'aud': 'valid-client-id'
        }
        
        # Step 3-4: Authenticate
        auth_response = client.post(
            "/auth/google",
            json={"id_token": "valid_integration_token"}
        )
        
        assert auth_response.status_code == 200
        jwt_token = auth_response.json()["access_token"]
        
        # Step 5: Use JWT token to access protected endpoint
        # (Example: Get user profile)
        profile_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        
        # Should be able to access protected resource
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == "integration@gmail.com"
        assert profile_data["display_name"] == "Integration Test User"
