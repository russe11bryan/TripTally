#!/usr/bin/env python3
"""
Simple test script to verify Redis CI system is working
"""

import redis
import requests
import time
from datetime import datetime

# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
API_BASE = "http://localhost:8000"

def test_redis():
    """Test Redis connection"""
    print("1. Testing Redis connection...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print("   ✓ Redis is running\n")
        return r
    except Exception as e:
        print(f"   ✗ Redis connection failed: {e}\n")
        return None

def test_redis_data(r):
    """Test if CI data exists in Redis"""
    print("2. Checking Redis data...")
    
    # Check for any current state keys
    now_keys = r.keys("ci:now:*")
    fcst_keys = r.keys("ci:fcst:*")
    
    print(f"   Current state keys: {len(now_keys)}")
    print(f"   Forecast keys: {len(fcst_keys)}")
    
    if len(now_keys) > 0:
        print("   ✓ CI data found in Redis")
        
        # Show sample data
        sample_key = now_keys[0]
        data = r.hgetall(sample_key)
        cam_id = sample_key.split(":")[-1]
        print(f"\n   Sample data for camera {cam_id}:")
        print(f"   - Timestamp: {data.get('ts', 'N/A')}")
        print(f"   - CI: {data.get('CI', 'N/A')}")
        print(f"   - Vehicles: {data.get('veh_count', 'N/A')}")
        print()
        return cam_id
    else:
        print("   ⚠ No CI data found in Redis")
        print("   → Is simple_ci_redis.py running?")
        print("   → Wait 2-3 minutes for first iteration\n")
        return None

def test_api_health():
    """Test API health endpoint"""
    print("3. Testing API health...")
    try:
        resp = requests.get(f"{API_BASE}/api/cameras/health", timeout=5)
        if resp.status_code == 200:
            print(f"   ✓ API is healthy: {resp.json()}\n")
            return True
        else:
            print(f"   ✗ API returned {resp.status_code}: {resp.text}\n")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to API at {API_BASE}")
        print("   → Is FastAPI running?")
        print("   → Run: uvicorn app.main:app --reload\n")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False

def test_api_now(cam_id):
    """Test /now endpoint"""
    print(f"4. Testing /api/cameras/{cam_id}/now...")
    try:
        resp = requests.get(f"{API_BASE}/api/cameras/{cam_id}/now", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print("   ✓ API endpoint working")
            print(f"   Response: {data}\n")
            return True
        else:
            print(f"   ✗ API returned {resp.status_code}: {resp.text}\n")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False

def test_api_forecast(cam_id):
    """Test /forecast endpoint"""
    print(f"5. Testing /api/cameras/{cam_id}/forecast...")
    try:
        resp = requests.get(f"{API_BASE}/api/cameras/{cam_id}/forecast", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print("   ✓ API endpoint working")
            horizons = data.get("horizons_min", [])
            forecasts = data.get("CI_forecast", [])
            print(f"   Horizons: {horizons[:5]}... (showing first 5)")
            print(f"   Forecasts: {forecasts[:5]}... (showing first 5)\n")
            return True
        else:
            print(f"   ✗ API returned {resp.status_code}: {resp.text}\n")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False

def main():
    print("=" * 60)
    print("CI Redis System Test")
    print("=" * 60)
    print()
    
    # Test Redis
    r = test_redis()
    if not r:
        print("FAILED: Cannot connect to Redis")
        return
    
    # Check data
    cam_id = test_redis_data(r)
    
    # Test API
    api_ok = test_api_health()
    
    if cam_id and api_ok:
        # Test endpoints
        test_api_now(cam_id)
        test_api_forecast(cam_id)
    elif not cam_id:
        print("Skipping API endpoint tests (no data in Redis yet)")
    elif not api_ok:
        print("Skipping API endpoint tests (API not running)")
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if cam_id and api_ok:
        print("✓ All tests passed!")
        print("\nYour CI system is working correctly!")
        print("\nNext steps:")
        print("  1. Check logs: watch simple_ci_redis.py output")
        print("  2. Monitor Redis: redis-cli MONITOR")
        print("  3. Try API: curl http://localhost:8000/api/cameras/{cam_id}/now")
    else:
        print("⚠ Some tests failed")
        print("\nTroubleshooting:")
        if not r:
            print("  1. Start Redis: redis-server")
        if not cam_id:
            print("  2. Start CI service: python start_simple_ci.py")
            print("     Wait 2-3 minutes for first iteration")
        if not api_ok:
            print("  3. Start FastAPI: uvicorn app.main:app --reload")
        print("\nSee QUICKSTART.md for detailed setup instructions")
    
    print()

if __name__ == "__main__":
    main()
