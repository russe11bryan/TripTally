"""
End-to-End Test: Traffic Improves Later - Wait Scenario

This test simulates a realistic scenario where:
- Current traffic is heavy (high CI)
- Traffic improves in 20-30 minutes (lower CI)
- System should recommend waiting

Test Strategy:
1. Use real camera locations from cam_id_lat_lon.json
2. Mock current traffic as congested
3. Mock future forecasts showing improvement
4. Verify optimizer recommends waiting
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.trafficcams.domain.route_models import Point
from app.services.trafficcams.domain.geospatial_service import GeospatialService
from app.services.trafficcams.domain.departure_time_optimizer import DepartureTimeOptimizer, ETACalculationStrategy
from app.services.trafficcams.domain.camera_loader import get_camera_loader
from app.services.trafficcams.models import Camera


def test_wait_scenario_e2e():
    """
    End-to-End Test: Traffic improves later, should recommend waiting
    
    Scenario:
    - Route: Marina Bay to Changi (Eastern Singapore)
    - Current time: Heavy traffic (CI = 0.75)
    - In 20 minutes: Traffic clears (CI = 0.35)
    - Expected: Recommend waiting ~20 minutes
    """
    
    print("\n" + "=" * 80)
    print("🧪 END-TO-END TEST: WAIT SCENARIO")
    print("=" * 80)
    
    # Test route using real camera locations from cam_id_lat_lon.json
    print("\n📍 Test Route Setup:")
    route_points = [
        Point(latitude=1.2958, longitude=103.8808),  # Near camera 3704 (Marina Bay area)
        Point(latitude=1.3200, longitude=103.9100),  # Near camera 5797 (Middle)
        Point(latitude=1.3400, longitude=103.9800),  # Near camera 3702 (Changi area)
    ]
    
    print(f"  Start:  Marina Bay area (1.2958, 103.8808)")
    print(f"  Via:    Central East (1.3200, 103.9100)")  
    print(f"  End:    Changi area (1.3400, 103.9800)")
    
    original_eta = 30  # 30 minutes baseline ETA
    print(f"\n⏱️  Original ETA: {original_eta} minutes")
    
    # Mock repository with realistic traffic data
    print("\n🚦 Mocking Traffic Conditions:")
    print("  Current (now):        HIGH CI = 0.75 (heavy congestion)")
    print("  Forecast (+10 min):   HIGH CI = 0.70 (still congested)")
    print("  Forecast (+20 min):   LOW CI = 0.35 (traffic clears!)")
    print("  Forecast (+30 min):   LOW CI = 0.30 (smooth traffic)")
    
    mock_repository = Mock()
    
    # Find cameras near route
    geospatial = GeospatialService()
    camera_loader = get_camera_loader()
    all_cameras = camera_loader.load_cameras()
    
    nearby_cameras = []
    for point in route_points:
        for camera in all_cameras:
            distance = geospatial.haversine_distance(
                point.latitude, point.longitude,
                camera.latitude, camera.longitude
            )
            if distance <= 0.5:  # 500m radius
                nearby_cameras.append(camera)
    
    nearby_cameras = list({cam.camera_id: cam for cam in nearby_cameras}.values())
    print(f"\n📷 Cameras found near route: {len(nearby_cameras)}")
    for cam in nearby_cameras[:5]:  # Show first 5
        print(f"  - Camera {cam.camera_id}: ({cam.latitude:.4f}, {cam.longitude:.4f})")
    
    if not nearby_cameras:
        print("\n⚠️  Warning: No cameras found near route. Using mock cameras.")
        # Create mock cameras if none found
        nearby_cameras = [
            Camera(camera_id="MOCK1", latitude=route_points[0].latitude, longitude=route_points[0].longitude),
            Camera(camera_id="MOCK2", latitude=route_points[1].latitude, longitude=route_points[1].longitude),
        ]
    
    # Mock current CI state (HIGH CONGESTION)
    def get_ci_state_mock(cam_id):
        """Return high CI for current traffic"""
        return {'CI': 0.75, 'timestamp': datetime.now()}
    
    # Mock forecast data (IMPROVEMENT IN 20 MINUTES)
    # Redis format: forecast dict with keys like "h_0", "h_10", "h_20" for horizons
    # Call pattern: for each time_slot, loop through all cameras calling get_forecast once per camera
    forecast_sequence = []
    
    # For each camera, create a forecast dict with all horizons
    for camera in nearby_cameras:
        forecast_dict = {}
        
        # Add forecast for each horizon
        for minutes in range(0, 121, 10):
            if minutes == 0:
                ci = 0.75  # Current: Heavy traffic
            elif minutes == 10:
                ci = 0.70  # +10 min: Still heavy
            elif minutes == 20:
                ci = 0.35  # +20 min: Traffic clears! (This is optimal)
            elif minutes == 30:
                ci = 0.30  # +30 min: Smooth traffic
            else:
                ci = 0.32  # +40 min onwards: Stay smooth
            
            forecast_dict[f'h_{minutes}'] = ci
        
        # The optimizer will call get_forecast many times for this camera (once per time slot)
        # Each call should return the full forecast dict
        # Since we check 13 time slots (0, 10, 20... 120) and have 4 cameras = 52 calls
        for _ in range(13):  # 13 time slots
            forecast_sequence.append(forecast_dict.copy())
    
    # Setup mocks
    def get_forecast_mock():
        if forecast_sequence:
            val = forecast_sequence.pop(0)
            return val
        return None
    
    mock_repository.get_ci_state.side_effect = lambda cam_id: get_ci_state_mock(cam_id)
    mock_repository.get_forecast.side_effect = lambda *args, **kwargs: get_forecast_mock()
    
    # Create optimizer with mocked repository
    optimizer = DepartureTimeOptimizer(
        repository=mock_repository,
        geospatial_service=geospatial,
        camera_loader=camera_loader
    )
    
    # Run optimization
    print("\n🔄 Running Optimization...")
    print("  Analyzing traffic patterns...")
    print("  Checking forecasts for next 2 hours...")
    print("  Evaluating 13 time slots (0, 10, 20, 30... 120 minutes)")
    
    result = optimizer.find_optimal_departure(
        route_points=route_points,
        original_eta_minutes=original_eta,
        search_radius_km=0.5,
        forecast_horizon_minutes=120,
        time_interval_minutes=10  # Check every 10 minutes
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 OPTIMIZATION RESULTS")
    print("=" * 80)
    
    print(f"\n🎯 Analysis Summary:")
    print(f"  Cameras analyzed:    {result.cameras_analyzed}")
    print(f"  Confidence score:    {result.confidence_score:.1%}")
    
    print(f"\n🚦 Traffic Comparison:")
    print(f"  Current average CI:  {result.current_average_ci:.2f} (congested)")
    print(f"  Optimal average CI:  {result.optimal_average_ci:.2f} (clear)")
    print(f"  CI improvement:      {((result.current_average_ci - result.optimal_average_ci) / result.current_average_ci * 100):.1f}%")
    
    print(f"\n⏰ Timing Recommendation:")
    print(f"  Best departure:      +{result.best_time_minutes_from_now} minutes from now")
    print(f"  Departure time:      {result.best_departure_time.strftime('%I:%M:%S %p')}")
    
    # Calculate ETAs using current 2-parameter method
    eta_calc = ETACalculationStrategy()
    
    current_eta = eta_calc.calculate_eta_from_ci(
        original_eta,
        result.current_average_ci
    )
    
    optimal_eta = eta_calc.calculate_eta_from_ci(
        original_eta,
        result.optimal_average_ci
    )
    
    print(f"\n🚗 ETA Analysis:")
    print(f"  Baseline ETA:        {original_eta} min (no traffic)")
    print(f"  Current ETA:         {current_eta} min (if leaving now)")
    print(f"  Optimized ETA:       {optimal_eta} min (if waiting)")
    print(f"  Time saved:          {current_eta - optimal_eta} min")
    print(f"  Wait time:           {result.best_time_minutes_from_now} min")
    print(f"  Net benefit:         {current_eta - optimal_eta - result.best_time_minutes_from_now} min")
    
    print(f"\n💡 Recommendation:")
    if result.best_time_minutes_from_now == 0:
        print("  ✅ Leave NOW! Traffic is already good.")
        recommendation = "LEAVE_NOW"
    elif result.best_time_minutes_from_now > 0:
        time_saved = current_eta - optimal_eta
        net_benefit = time_saved - result.best_time_minutes_from_now
        
        if net_benefit > 3:
            print(f"  ⏰ WAIT {result.best_time_minutes_from_now} minutes!")
            print(f"     Traffic will clear significantly.")
            print(f"     You'll save {time_saved} minutes of travel time.")
            print(f"     Net benefit: {net_benefit} minutes overall.")
            recommendation = "WAIT"
        elif net_benefit > 0:
            print(f"  ⚖️  Slight benefit to wait {result.best_time_minutes_from_now} minutes")
            print(f"     Net benefit: {net_benefit} minutes")
            recommendation = "SLIGHT_WAIT"
        else:
            print("  ➡️  Similar travel time either way")
            recommendation = "NEUTRAL"
    
    # Validation assertions
    print("\n" + "=" * 80)
    print("✅ TEST VALIDATION")
    print("=" * 80)
    
    assertions_passed = []
    assertions_failed = []
    
    # Test 1: Should recommend waiting (not leaving now)
    if result.best_time_minutes_from_now > 0:
        assertions_passed.append("✓ Recommends waiting (not leaving immediately)")
    else:
        assertions_failed.append("✗ Should recommend waiting, but suggests leaving now")
    
    # Test 2: Wait time should be around 20 minutes (when traffic clears)
    if 15 <= result.best_time_minutes_from_now <= 30:
        assertions_passed.append(f"✓ Wait time is reasonable: {result.best_time_minutes_from_now} min (expected ~20)")
    else:
        assertions_failed.append(f"✗ Wait time unexpected: {result.best_time_minutes_from_now} min (expected 15-30)")
    
    # Test 3: Optimal CI should be lower than current CI
    if result.optimal_average_ci < result.current_average_ci:
        improvement = ((result.current_average_ci - result.optimal_average_ci) / result.current_average_ci * 100)
        assertions_passed.append(f"✓ Traffic improves: {improvement:.1f}% reduction in CI")
    else:
        assertions_failed.append("✗ Optimal CI should be lower than current CI")
    
    # Test 4: Should save time overall
    time_saved = current_eta - optimal_eta
    if time_saved > 0:
        assertions_passed.append(f"✓ Saves travel time: {time_saved} minutes")
    else:
        assertions_failed.append("✗ Should save travel time by waiting")
    
    # Test 5: Confidence should be reasonable
    if result.confidence_score >= 0.3:
        assertions_passed.append(f"✓ Confidence is reasonable: {result.confidence_score:.1%}")
    else:
        assertions_failed.append(f"✗ Confidence too low: {result.confidence_score:.1%}")
    
    # Print results
    print("\n✅ Passed Assertions:")
    for assertion in assertions_passed:
        print(f"  {assertion}")
    
    if assertions_failed:
        print("\n❌ Failed Assertions:")
        for assertion in assertions_failed:
            print(f"  {assertion}")
    
    print("\n" + "=" * 80)
    
    # Final verdict
    test_passed = len(assertions_failed) == 0
    
    if test_passed:
        print("🎉 END-TO-END TEST PASSED!")
        print("   The optimizer correctly recommends waiting when traffic improves later.")
    else:
        print("❌ END-TO-END TEST FAILED!")
        print(f"   {len(assertions_failed)} assertion(s) failed.")
    
    print("=" * 80 + "\n")
    
    return test_passed


if __name__ == "__main__":
    try:
        success = test_wait_scenario_e2e()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 TEST CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
