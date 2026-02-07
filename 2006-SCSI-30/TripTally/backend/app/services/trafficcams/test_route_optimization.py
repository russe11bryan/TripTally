"""
Route Optimization Service Tests
Unit tests for route optimization components
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from domain.route_models import Point, LineString
from domain.geospatial_service import GeospatialService
from domain.camera_loader import get_camera_loader
from .models import Camera


def test_camera_loader():
    """Test camera data loading"""
    print("\n[TEST] Camera Data Loader")
    
    loader = get_camera_loader()
    cameras = loader.load_cameras()
    
    print(f"  Loaded cameras: {len(cameras)}")
    assert len(cameras) > 0, "Should load at least some cameras"
    
    # Test first camera
    first_cam = cameras[0]
    print(f"  First camera: {first_cam.camera_id} at ({first_cam.latitude:.4f}, {first_cam.longitude:.4f})")
    assert first_cam.camera_id is not None
    assert -90 <= first_cam.latitude <= 90
    assert -180 <= first_cam.longitude <= 180
    
    # Test get by ID
    cam = loader.get_camera_by_id(first_cam.camera_id)
    assert cam is not None
    assert cam.camera_id == first_cam.camera_id
    
    # Test get IDs
    cam_ids = loader.get_camera_ids()
    assert len(cam_ids) == len(cameras)
    
    print("  ✓ Camera loader works")


def test_haversine_distance():
    """Test distance calculation"""
    print("\n[TEST] Haversine Distance Calculation")
    
    service = GeospatialService()
    
    # Singapore: Orchard Road to Marina Bay (roughly 3-4 km)
    dist = service.haversine_distance(
        1.3048, 103.8318,  # Orchard Road
        1.2806, 103.8611   # Marina Bay
    )
    
    print(f"  Distance: {dist:.2f} km")
    assert 3.0 < dist < 5.0, f"Expected 3-5 km, got {dist:.2f}"
    print("  ✓ Distance calculation correct")


def test_point_to_line_distance():
    """Test point-to-line distance"""
    print("\n[TEST] Point to Line Distance")
    
    service = GeospatialService()
    
    # Simple test: point on line should have zero distance
    dist, t = service.point_to_line_distance(
        1.35, 103.82,      # Point
        1.34, 103.81,      # Line start
        1.36, 103.83       # Line end
    )
    
    print(f"  Distance: {dist*1000:.1f} meters")
    print(f"  Position on segment: {t:.2f}")
    assert dist < 0.01, f"Expected near-zero distance, got {dist:.4f}"
    print("  ✓ Point-to-line calculation correct")


def test_find_cameras_along_route():
    """Test camera finding along route"""
    print("\n[TEST] Find Cameras Along Route")
    
    service = GeospatialService()
    
    # Create test route (north-south line in Singapore)
    route = LineString([
        Point(1.35, 103.82),
        Point(1.36, 103.82),
        Point(1.37, 103.82)
    ])
    
    # Create test cameras
    cameras = [
        Camera("near_1", 1.355, 103.82, "url1"),   # Very close
        Camera("near_2", 1.365, 103.82, "url2"),   # Very close
        Camera("far_1", 1.35, 103.90, "url3"),     # Far away
        Camera("far_2", 1.40, 103.82, "url4")      # Outside route
    ]
    
    # Find cameras within 1km
    result = service.find_cameras_along_route(route, cameras, 1.0)
    
    print(f"  Cameras found: {len(result)}")
    for cam in result:
        print(f"    - {cam.camera_id}: {cam.distance_to_route:.0f}m, "
              f"position {cam.position_on_route:.2f}")
    
    assert len(result) >= 2, f"Expected at least 2 cameras, got {len(result)}"
    assert result[0].position_on_route < result[-1].position_on_route, \
        "Cameras should be sorted by position"
    print("  ✓ Camera finding correct")


def test_calculate_route_length():
    """Test route length calculation"""
    print("\n[TEST] Calculate Route Length")
    
    service = GeospatialService()
    
    # Create route with known distances
    route = LineString([
        Point(1.30, 103.80),
        Point(1.31, 103.80),  # ~1.1 km north
        Point(1.31, 103.81)   # ~1.1 km east
    ])
    
    length = service.calculate_route_length(route)
    
    print(f"  Route length: {length:.2f} km")
    assert 2.0 < length < 3.0, f"Expected ~2.2 km, got {length:.2f}"
    print("  ✓ Route length calculation correct")


def test_traffic_level_classification():
    """Test CI to traffic level conversion"""
    print("\n[TEST] Traffic Level Classification")
    
    from domain.route_models import TrafficLevel
    
    test_cases = [
        (0.1, TrafficLevel.FREE_FLOW),
        (0.4, TrafficLevel.LIGHT),
        (0.6, TrafficLevel.MODERATE),
        (0.8, TrafficLevel.HEAVY),
        (0.95, TrafficLevel.SEVERE)
    ]
    
    for ci, expected in test_cases:
        level = TrafficLevel.from_ci(ci)
        print(f"  CI {ci:.2f} → {level.value}")
        assert level == expected, f"Expected {expected}, got {level}"
    
    print("  ✓ Traffic classification correct")


def test_route_models():
    """Test domain models"""
    print("\n[TEST] Domain Models")
    
    from domain.route_models import (
        Point, LineString, RouteCameraInfo, 
        CameraTrafficInfo, DepartureOption
    )
    
    # Test Point
    p = Point(1.35, 103.82)
    assert p.latitude == 1.35
    assert p.longitude == 103.82
    print("  ✓ Point model works")
    
    # Test LineString
    ls = LineString([p, Point(1.36, 103.83)])
    coords = ls.to_coordinates()
    assert len(coords) == 2
    assert coords[0] == (1.35, 103.82)
    print("  ✓ LineString model works")
    
    # Test RouteCameraInfo
    rci = RouteCameraInfo("cam1", 1.35, 103.82, 100.0, 0.5)
    assert rci.camera_id == "cam1"
    assert rci.distance_to_route == 100.0
    print("  ✓ RouteCameraInfo model works")
    
    # Test CameraTrafficInfo
    cti = CameraTrafficInfo("cam1", 0.5, 0.6, datetime.now())
    assert cti.current_ci == 0.5
    assert cti.forecast_ci == 0.6
    print("  ✓ CameraTrafficInfo model works")
    
    # Test DepartureOption
    do = DepartureOption(
        departure_time=datetime.now(),
        minutes_from_now=30,
        average_ci=0.5,
        max_ci=0.7,
        estimated_travel_time_minutes=25.0,
        new_eta=datetime.now(),
        confidence_score=0.8
    )
    assert do.minutes_from_now == 30
    assert do.confidence_score == 0.8
    print("  ✓ DepartureOption model works")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("ROUTE OPTIMIZATION SERVICE TESTS")
    print("=" * 70)
    
    tests = [
        test_camera_loader,
        test_haversine_distance,
        test_point_to_line_distance,
        test_find_cameras_along_route,
        test_calculate_route_length,
        test_traffic_level_classification,
        test_route_models
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
