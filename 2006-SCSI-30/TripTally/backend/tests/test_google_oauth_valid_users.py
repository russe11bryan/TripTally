"""
Test script for Google OAuth with VALID tokens.
Tests new user registration and existing user login scenarios.

IMPORTANT: You need to provide REAL valid Google ID tokens to run these tests.
"""

import requests

# Base URL for your backend API
BASE_URL = "http://localhost:8000"

def test_valid_token_new_user():
    """
    Test Google OAuth with a valid token for a NEW user.
    
    To run this test:
    1. Create a NEW Google account (or use one that hasn't signed into your app)
    2. Sign in to your mobile app with this Google account
    3. Intercept the network request to get the id_token
    4. Paste the token below
    5. Run this script
    
    Expected Result:
    - Status Code: 200 OK
    - Response contains access_token (JWT)
    - New user account is created in database
    """
    print("\n" + "="*70)
    print("Test: Valid Token - NEW USER Registration")
    print("-"*70)
    
    # REPLACE THIS with a real valid Google ID token from a NEW user
    valid_token_new_user = "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE_FOR_NEW_USER"
    
    if valid_token_new_user == "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE_FOR_NEW_USER":
        print("SKIPPED: You need to provide a valid Google ID token")
        print("\n How to get the token:")
        print("   1. Create a NEW Google account (one that hasn't used your app)")
        print("   2. Open your mobile app")
        print("   3. Sign in with the new Google account")
        print("   4. Use React Native Debugger or Charles Proxy to intercept the request")
        print("   5. Copy the id_token from the request body")
        print("   6. Paste it in this script and run again")
        return
    
    # Make request to backend
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": valid_token_new_user}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Assertions
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            print("PASS: New user registered successfully!")
            print(f"   - Received access_token (JWT)")
            print(f"   - Token length: {len(data['access_token'])} characters")
            
            # Try using the token to get user info
            print("\nVerifying the token by fetching user profile...")
            profile_response = requests.get(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f"Token works! User profile:")
                print(f"   - Email: {profile.get('email')}")
                print(f"   - Display Name: {profile.get('display_name')}")
                print(f"   - User ID: {profile.get('id')}")
            else:
                print(f"Token verification failed: {profile_response.status_code}")
        else:
            print("FAIL: Response missing access_token")
    else:
        print(f"FAIL: Expected 200, got {response.status_code}")
        print(f"   Error: {response.json()}")


def test_valid_token_existing_user():
    """
    Test Google OAuth with a valid token for an EXISTING user.
    
    To run this test:
    1. Use a Google account that has ALREADY signed into your app before
    2. Sign in again with the same Google account
    3. Intercept the network request to get the id_token
    4. Paste the token below
    5. Run this script
    
    Expected Result:
    - Status Code: 200 OK
    - Response contains access_token (JWT)
    - Returns existing user (no duplicate created)
    """
    print("\n" + "="*70)
    print("Test: Valid Token - EXISTING USER Login")
    print("-"*70)
    
    # REPLACE THIS with a real valid Google ID token from an EXISTING user
    valid_token_existing_user = "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE_FOR_EXISTING_USER"
    
    if valid_token_existing_user == "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE_FOR_EXISTING_USER":
        print("SKIPPED: You need to provide a valid Google ID token")
        print("\n How to get the token:")
        print("   1. Use a Google account that has ALREADY signed into your app")
        print("   2. Open your mobile app")
        print("   3. Sign in again with the SAME Google account")
        print("   4. Use React Native Debugger or Charles Proxy to intercept the request")
        print("   5. Copy the id_token from the request body")
        print("   6. Paste it in this script and run again")
        return
    
    # Make request to backend
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": valid_token_existing_user}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Assertions
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            print("PASS: Existing user logged in successfully!")
            print(f"   - Received access_token (JWT)")
            print(f"   - Token length: {len(data['access_token'])} characters")
            
            # Try using the token to get user info
            print("\n🔍 Verifying the token by fetching user profile...")
            profile_response = requests.get(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f"Token works! User profile:")
                print(f"   - Email: {profile.get('email')}")
                print(f"   - Display Name: {profile.get('display_name')}")
                print(f"   - User ID: {profile.get('id')}")
                print(f"   - This should match the previous user account")
            else:
                print(f"Token verification failed: {profile_response.status_code}")
        else:
            print(" FAIL: Response missing access_token")
    else:
        print(f"FAIL: Expected 200, got {response.status_code}")
        print(f"   Error: {response.json()}")


def test_complete_oauth_flow():
    """
    Test the complete OAuth flow with proper sequence.
    This simulates what happens when a user signs in twice.
    """
    print("\n" + "="*70)
    print("Test: Complete OAuth Flow (Same User, Two Sign-ins)")
    print("-"*70)
    
    # REPLACE THIS with a real valid Google ID token
    # Note: You can use the same token twice since it represents the same user
    valid_token = "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE"
    
    if valid_token == "PASTE_YOUR_VALID_GOOGLE_ID_TOKEN_HERE":
        print("SKIPPED: You need to provide a valid Google ID token")
        print("\nThis test verifies that:")
        print("   1. First sign-in creates a new user account")
        print("   2. Second sign-in with same Google account returns existing user")
        print("   3. No duplicate accounts are created")
        return
    
    print("\nFirst Sign-in (Should create new user):")
    response1 = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": valid_token}
    )
    print(f"Status Code: {response1.status_code}")
    if response1.status_code == 200:
        token1 = response1.json().get("access_token")
        print(f" Got access token (length: {len(token1)})")
        
        # Get user ID from first sign-in
        profile1 = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        ).json()
        user_id_1 = profile1.get('id')
        print(f"   User ID: {user_id_1}")
        print(f"   Email: {profile1.get('email')}")
    else:
        print(f" Failed: {response1.json()}")
        return
    
    print("\nSecond Sign-in (Should return existing user):")
    response2 = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": valid_token}
    )
    print(f"Status Code: {response2.status_code}")
    if response2.status_code == 200:
        token2 = response2.json().get("access_token")
        print(f"Got access token (length: {len(token2)})")
        
        # Get user ID from second sign-in
        profile2 = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        ).json()
        user_id_2 = profile2.get('id')
        print(f"   User ID: {user_id_2}")
        print(f"   Email: {profile2.get('email')}")
        
        # Verify same user
        if user_id_1 == user_id_2:
            print("\n PASS: Both sign-ins returned the SAME user!")
            print("   No duplicate accounts were created.")
        else:
            print("\n FAIL: Different user IDs!")
            print(f"   First: {user_id_1}")
            print(f"   Second: {user_id_2}")
    else:
        print(f"Failed: {response2.json()}")


if __name__ == "__main__":
    print("\nTesting Google OAuth with VALID Tokens")
    print("="*70)
    print("\nIMPORTANT: These tests require REAL valid Google ID tokens!")
    print("   You need to get tokens from your mobile app by intercepting")
    print("   the network requests during Google Sign-In.")
    print("\n Setup Instructions:")
    print("   1. Make sure your backend is running on http://localhost:8000")
    print("   2. Open your React Native mobile app")
    print("   3. Enable React Native Debugger or Charles Proxy")
    print("   4. Sign in with Google")
    print("   5. Copy the id_token from the intercepted request")
    print("   6. Paste it into this script")
    print("   7. Run the script again")
    print("="*70)
    
    # Run tests
    test_valid_token_new_user()
    test_valid_token_existing_user()
    test_complete_oauth_flow()
    
    print("\n" + "="*70)
    print(" Test Suite Complete!")
    print("\n Remember: Tokens expire after ~1 hour, so you'll need fresh tokens")
    print("   each time you run these tests.")
    print("="*70 + "\n")
