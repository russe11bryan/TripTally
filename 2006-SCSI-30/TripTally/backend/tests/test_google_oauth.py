"""
Test script for Google OAuth token validation.
Tests different invalid token scenarios.
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_google_oauth():
    """Test various Google OAuth token validation scenarios."""
    
    print("Testing Google OAuth Token Validation\n")
    print("=" * 70)
    
    # Test 1: Empty Token
    print("\n Test 1: Empty Token")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": ""}
    )
    print(f"Request: Empty string token")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 401 Unauthorized")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 401 else f" FAIL")
    
    # Test 2: Malformed Token (Invalid Format)
    print("\nTest 2: Malformed Token (Invalid JWT Format)")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": "not-a-valid-jwt-token"}
    )
    print(f"Request: 'not-a-valid-jwt-token'")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 401 Unauthorized")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 401 else f"FAIL")
    
    # Test 3: Fake JWT Token (Valid format but invalid signature)
    print("\nTest 3: Fake JWT Token (Valid format, invalid signature)")
    print("-" * 70)
    fake_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid-signature-here"
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": fake_token}
    )
    print(f"Request: Fake JWT with invalid signature")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 401 Unauthorized")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 401 else f" FAIL")
    
    # Test 4: Expired Token (you need to generate a real expired token)
    print("\nTest 4: Expired Token")
    print("-" * 70)
    print("  To test expired token:")
    print("   1. Get a valid Google ID token from your app")
    print("   2. Wait for it to expire (typically 1 hour)")
    print("   3. Replace the token below and uncomment the test")
    print("   4. Expected result: 401 Unauthorized with 'Token expired' message")
    # expired_token = "PASTE_REAL_EXPIRED_TOKEN_HERE"
    # response = requests.post(
    #     f"{BASE_URL}/auth/google",
    #     json={"id_token": expired_token}
    # )
    # print(f"Status Code: {response.status_code}")
    # print(f"Response: {response.json()}")
    print("  SKIPPED (need real expired token)")
    
    # Test 5: Token with Wrong Client ID
    print("\n Test 5: Token with Wrong Client ID")
    print("-" * 70)
    print("  To test wrong client ID:")
    print("   1. Get a valid Google ID token from a DIFFERENT Google Cloud project")
    print("   2. Replace the token below and uncomment the test")
    print("   3. Expected result: 401 Unauthorized with 'client_id mismatch' message")
    # wrong_client_token = "PASTE_TOKEN_FROM_DIFFERENT_PROJECT_HERE"
    # response = requests.post(
    #     f"{BASE_URL}/auth/google",
    #     json={"id_token": wrong_client_token}
    # )
    # print(f"Status Code: {response.status_code}")
    # print(f"Response: {response.json()}")
    print(" SKIPPED (need token from different project)")
    
    # Test 6: Missing Token Field
    print("\n Test 6: Missing Token Field (No id_token in request)")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={}
    )
    print(f"Request: Empty JSON object")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 422 Unprocessable Entity (Pydantic validation error)")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 422 else f" FAIL")
    
    # Test 7: Null Token
    print("\nTest 7: Null Token")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": None}
    )
    print(f"Request: null token")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 422 Unprocessable Entity")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 422 else f" FAIL")
    # Test 8: Very Long Invalid Token
    
    print("\n Test 8: Very Long Invalid Token")
    print("-" * 70)
    long_token = "a" * 10000  # 10,000 character string
    response = requests.post(
        f"{BASE_URL}/auth/google",
        json={"id_token": long_token}
    )
    print(f"Request: {len(long_token)} character string")
    print(f"Status Code: {response.status_code}")
    print(f"Expected: 401 Unauthorized")
    print(f"Response: {response.json()}")
    print(f" PASS" if response.status_code == 401 else f" FAIL")
    
    print("\n" + "=" * 70)
    print(" Test Suite Complete!")
    


if __name__ == "__main__":
    try:
        test_google_oauth()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to backend server")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"Unexpected error: {e}")
