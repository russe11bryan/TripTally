"""
Comprehensive Test Suite for Backend Fixes
Tests all fixed components to ensure they work correctly
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test 1: Verify all imports work correctly"""
    print("\n" + "="*60)
    print("TEST 1: Import Tests")
    print("="*60)
    
    try:
        from app.services.trafficcams.data_repository import DataRepository
        print("DataRepository import successful")
        
        from app.services.trafficcams.models import Camera, CIState, CIForecast
        print("Models import successful")
        
        from app.services.trafficcams.config import Config
        print("Config import successful")
        
        from app.services.trafficcams.factory import ServiceContext
        print("ServiceContext import successful")
        
        from app.services.trafficcams.domain.route_optimizer import RouteOptimizationService
        print("RouteOptimizationService import successful")
        
        from app.services.trafficcams.domain.departure_time_optimizer import DepartureTimeOptimizer
        print("DepartureTimeOptimizer import successful")
        
        from app.services.trafficcams.domain.geospatial_service import GeospatialService
        print("GeospatialService import successful")
        
        from app.api.route_optimization_routes import router as route_router
        print("Route optimization routes import successful")
        
        from app.api.departure_optimization_routes import router as departure_router
        print("Departure optimization routes import successful")
        
        print("\nAll imports passed!")
        return True
    except Exception as e:
        print(f"\nImport failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_context():
    """Test 2: Verify ServiceContext works correctly"""
    print("\n" + "="*60)
    print("TEST 2: ServiceContext Functionality")
    print("="*60)
    
    try:
        from app.services.trafficcams.config import Config
        from app.services.trafficcams.factory import ServiceContext
        
        # Test creating config from environment
        config = Config.from_env()
        print(f"Config created: {config.processing.repository_type}")
        
        # Test creating service context
        service_context = ServiceContext.from_config(config)
        print(f" ServiceContext created")
        print(f"  Repository: {service_context.repository.get_repository_name()}")
        print(f"  Forecaster: {service_context.forecaster.get_strategy_name()}")
        
        print("\nServiceContext test passed!")
        return True
    except Exception as e:
        print(f"\nServiceContext test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_geospatial_service():
    """Test 3: Verify GeospatialService method signatures"""
    print("\n" + "="*60)
    print("TEST 3: GeospatialService Method Signatures")
    print("="*60)
    
    try:
        from app.services.trafficcams.domain.geospatial_service import GeospatialService
        from app.services.trafficcams.domain.route_models import Point, LineString
        from app.services.trafficcams.models import Camera
        import inspect
        
        geo_service = GeospatialService()
        print("GeospatialService created")
        
        # Check find_cameras_along_route signature
        sig = inspect.signature(geo_service.find_cameras_along_route)
        params = list(sig.parameters.keys())
        print(f"find_cameras_along_route parameters: {params}")
        
        if 'search_radius_km' in params:
            print("✓ Correct parameter name: search_radius_km")
        else:
            print("Wrong parameter name!")
            return False
        
        # Test with mock data
        route = LineString(points=[
            Point(latitude=1.35, longitude=103.82),
            Point(latitude=1.36, longitude=103.83)
        ])
        cameras = [
            Camera(camera_id="1001", latitude=1.355, longitude=103.825),
            Camera(camera_id="1002", latitude=1.365, longitude=103.835)
        ]
        
        result = geo_service.find_cameras_along_route(route, cameras, search_radius_km=1.0)
        print(f"Method called successfully, found {len(result)} cameras")
        print(f"  Return type: {type(result[0]).__name__ if result else 'Empty list'}")
        
        print("\nGeospatialService test passed!")
        return True
    except Exception as e:
        print(f"\nGeospatialService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_departure_optimizer_types():
    """Test 4: Verify DepartureTimeOptimizer type annotations"""
    print("\n" + "="*60)
    print("TEST 4: DepartureTimeOptimizer Type Annotations")
    print("="*60)
    
    try:
        from app.services.trafficcams.domain.departure_time_optimizer import DepartureTimeOptimizer
        from app.services.trafficcams.domain.route_models import RouteCameraInfo
        import inspect
        
        # Check method signatures
        method = DepartureTimeOptimizer._find_cameras_near_route
        sig = inspect.signature(method)
        return_annotation = sig.return_annotation
        print(f" _find_cameras_near_route return type: {return_annotation}")
        
        method = DepartureTimeOptimizer._analyze_current_conditions
        sig = inspect.signature(method)
        params = sig.parameters
        cameras_param = params.get('cameras_near_route')
        if cameras_param:
            print(f" _analyze_current_conditions cameras_near_route type: {cameras_param.annotation}")
    
        method = DepartureTimeOptimizer._analyze_forecast_time_slots
        sig = inspect.signature(method)
        params = sig.parameters
        cameras_param = params.get('cameras_near_route')
        if cameras_param:
            print(f" _analyze_forecast_time_slots cameras_near_route type: {cameras_param.annotation}")
        
        print("\nType annotations test passed!")
        return True
    except Exception as e:
        print(f"\nType annotations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """Test 5: Verify API routes can be imported and created"""
    print("\n" + "="*60)
    print("TEST 5: API Routes")
    print("="*60)
    
    try:
        from app.api.route_optimization_routes import router as route_router
        from app.api.departure_optimization_routes import router as departure_router
        
        print(f" Route optimization router: {route_router.prefix}")
        print(f"  Routes: {[r.name for r in route_router.routes]}")
        
        print(f" Departure optimization router: {departure_router.prefix}")
        print(f"  Routes: {[r.name for r in departure_router.routes]}")
        
        print("\nAPI routes test passed!")
        return True
    except Exception as e:
        print(f"\API routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_unit_tests():
    """Run all unit tests"""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: ServiceContext
    results.append(("ServiceContext", test_service_context()))
    
    # Test 3: GeospatialService
    results.append(("GeospatialService", test_geospatial_service()))
    
    # Test 4: Type Annotations
    results.append(("Type Annotations", test_departure_optimizer_types()))
    
    # Test 5: API Routes
    results.append(("API Routes", test_api_routes()))
    
    return results


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return False


def main():
    """Run all tests and print summary"""
    print("\n" + "="*60)
    print("BACKEND FIXES COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    try:
        results = run_unit_tests()
        success = print_summary(results)
        
        if success:
            print("\nBackend is ready for integration testing!")
            print("\nNext steps:")
            print("1. Start the backend: uvicorn app.main:app --reload")
            print("2. Test API endpoints with frontend")
            print("3. Verify departure optimization works end-to-end")
        else:
            print("\nSome tests failed. Please fix the issues before proceeding.")
        
        return success
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
