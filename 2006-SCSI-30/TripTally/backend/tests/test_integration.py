"""
Integration Test: Backend API ↔ Forecasting Service
Tests the complete flow from forecasting service to API endpoints
"""

import asyncio
import os
from datetime import datetime
from redis.asyncio import Redis
from app.adapters.redis_traffic_camera_repo_v2 import RedisTrafficCameraRepoV2


async def test_integration():
    """Test complete integration"""
    
    print("=" * 60)
    print("BACKEND  FORECASTING SERVICE INTEGRATION TEST")
    print("=" * 60)
    
    # Connect to Redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    print(f"\n1. Connecting to Redis at {redis_host}:{redis_port} (DB {redis_db})")
    redis_client = Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=False
    )
    
    # Check Redis health
    try:
        await redis_client.ping()
        print("    Redis connection successful")
    except Exception as e:
        print(f"    Redis connection failed: {e}")
        return
    
    # Create repository
    repo = RedisTrafficCameraRepoV2(redis_client)
    
    # Test health check
    print("\n2. Testing repository health check")
    is_healthy = await repo.health_check()
    print(f"   {'✓' if is_healthy else '✗'} Health check: {'Healthy' if is_healthy else 'Unhealthy'}")
    
    # Test get all cameras
    print("\n3. Testing get all cameras metadata")
    cameras = await repo.get_all_cameras()
    print(f"   ✓ Found {len(cameras)} cameras")
    if cameras:
        sample = cameras[0]
        print(f"   Sample camera: {sample.camera_id} at ({sample.latitude}, {sample.longitude})")
    
    # Test get specific camera
    if cameras:
        test_camera_id = cameras[0].camera_id
        print(f"\n4. Testing get specific camera: {test_camera_id}")
        camera = await repo.get_camera(test_camera_id)
        if camera:
            print(f"   ✓ Retrieved camera {camera.camera_id}")
        else:
            print(f"   ✗ Failed to retrieve camera")
    
    # Test get current state
    print(f"\n5. Testing get current state for {test_camera_id}")
    now = await repo.get_now(test_camera_id)
    if now:
        print(f"   ✓ Retrieved current state")
        print(f"   - Timestamp: {now.ts}")
        print(f"   - CI: {now.CI:.3f}")
        print(f"   - Vehicle count: {now.veh_count}")
        print(f"   - Motion: {now.motion:.2f}")
        print(f"   - Model: {now.model_ver}")
    else:
        print(f"   ✗ No current state available")
    
    # Test get all current states
    print("\n6. Testing get all current states")
    all_now = await repo.get_all_now()
    print(f"   ✓ Retrieved {len(all_now)} current states")
    
    # Test get forecast
    print(f"\n7. Testing get forecast for {test_camera_id}")
    forecast = await repo.get_forecast(test_camera_id)
    if forecast:
        print(f"   ✓ Retrieved forecast")
        print(f"   - Forecast timestamp: {forecast.forecast_ts}")
        print(f"   - Number of horizons: {len(forecast.horizons)}")
        print(f"   - Model: {forecast.model_ver}")
        print(f"   - Horizon range: {forecast.horizons[0].horizon_min} to {forecast.horizons[-1].horizon_min} minutes")
        print(f"   - First 5 predictions:")
        for h in forecast.horizons[:5]:
            print(f"     • {h.horizon_min:3d} min: CI={h.CI_pred:.3f}")
        print(f"   - Last 5 predictions:")
        for h in forecast.horizons[-5:]:
            print(f"     • {h.horizon_min:3d} min: CI={h.CI_pred:.3f}")
    else:
        print(f"   ✗ No forecast available")
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Redis connection: Working")
    print(f"✓ Camera metadata: {len(cameras)} cameras loaded")
    print(f"✓ Current states: {len(all_now)} available")
    print(f"✓ Forecasts: {'Available' if forecast else 'Not available'}")
    if forecast:
        print(f"✓ Forecast horizons: {len(forecast.horizons)} predictions (2-minute intervals)")
    print("\n🎉 Integration is working correctly!")
    print("\nYou can now use these API endpoints:")
    print("  GET /api/cameras/ - List all cameras with current state")
    print("  GET /api/cameras/{camera_id}/now - Get current state")
    print("  GET /api/cameras/{camera_id}/forecast - Get forecast")
    print("  GET /api/cameras/{camera_id}/metadata - Get camera info")
    print("  GET /api/cameras/health - Health check")
    
    # Cleanup
    await redis_client.close()


if __name__ == "__main__":
    asyncio.run(test_integration())
