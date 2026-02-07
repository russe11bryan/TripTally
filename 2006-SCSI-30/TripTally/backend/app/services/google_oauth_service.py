"""
Google OAuth Service for handling Google Sign-In authentication.
"""
from typing import Optional
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from app.models.account import User
from app.models.saved_list import SavedList
from app.ports.user_repo import UserRepository


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    def __init__(self, user_repo: UserRepository, google_client_id: str, ios_client_id: str = "", saved_list_repo=None):
        self.user_repo = user_repo
        self.google_client_id = google_client_id
        self.ios_client_id = ios_client_id
        self.saved_list_repo = saved_list_repo
    
    def verify_google_token(self, token: str) -> Optional[dict]:
        """
        Verify Google ID token and return user info.
        
        Args:
            token: Google ID token from the client
            
        Returns:
            dict with user info (sub, email, name, picture) or None if invalid
        """
        # Try verifying with web client ID first
        idinfo = self._try_verify_token(token, self.google_client_id)
        
        # If that fails and we have an iOS client ID, try that
        if not idinfo and self.ios_client_id:
            idinfo = self._try_verify_token(token, self.ios_client_id)
        
        return idinfo
    
    def _try_verify_token(self, token: str, client_id: str) -> Optional[dict]:
        """Helper method to try verifying a token with a specific client ID."""
        try:
            print(f"[GoogleOAuth] Attempting to verify token with client_id: {client_id[:20]}...")
            
            # Verify the token with clock skew tolerance (10 seconds)
            # This helps handle slight time differences between client/server clocks
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                client_id,
                clock_skew_in_seconds=10
            )
            
            print(f"[GoogleOAuth] Token verified successfully! User: {idinfo.get('email')}")
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                print(f"[GoogleOAuth] Invalid issuer: {idinfo['iss']}")
                return None
                
            return idinfo
            
        except ValueError as e:
            # Invalid token for this client ID
            print(f"[GoogleOAuth] Token verification failed with client_id {client_id[:20]}...: {str(e)}")
            return None
        except Exception as e:
            print(f"[GoogleOAuth] Unexpected error verifying token: {str(e)}")
            return None
    
    def authenticate_or_create_user(self, google_id: str, email: str, display_name: str) -> User:
        """
        Authenticate existing user or create new user from Google profile.
        
        Args:
            google_id: Google user ID (sub claim from token)
            email: User's email from Google
            display_name: User's display name from Google
            
        Returns:
            User object (either existing or newly created)
        """
        # First, try to find user by Google ID
        user = self.user_repo.get_by_google_id(google_id)
        
        if user:
            return user
        
        # If not found by Google ID, check if email already exists
        user = self.user_repo.get_by_email(email)
        
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            return self.user_repo.update(user)
        
        # Create new user
        username = email.split('@')[0]  # Generate username from email
        
        # Ensure username is unique
        existing = self.user_repo.get_by_username(username)
        if existing:
            # Add random suffix if username exists
            import random
            username = f"{username}{random.randint(1000, 9999)}"
        
        new_user = User(
            id=None,
            email=email,
            username=username,
            hashed_password="",  # No password for Google sign-in users
            display_name=display_name,
            google_id=google_id,
            contact_number="",
            status="active"
        )
        
        created_user = self.user_repo.add(new_user)
        
        # Create default "Favourites" list for the new user
        if self.saved_list_repo:
            favourites = SavedList(
                id=None,
                user_id=created_user.id,
                name="Favourites",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.saved_list_repo.add(favourites)
        
        return created_user
