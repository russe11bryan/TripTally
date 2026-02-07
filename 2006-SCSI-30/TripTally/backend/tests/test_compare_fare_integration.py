"""
Integration tests for the /metrics/compare endpoint with public transport fare calculations
These tests verify that the compare endpoint correctly calculates and returns public transport fares
"""
import requests
import json


BASE_URL = "http://localhost:8000"


def test_compare_endpoint_with_public_transport():
    """Test that the compare endpoint returns public transport fares"""
    print("\n" + "="*80)
    print("TEST 1: Compare endpoint returns public transport fares")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 37.0,
            "route_polyline": "test",
            "origin": "1.3483,103.6831",  # NTU
            "destination": "1.3521,103.8198",  # Paya Lebar
            "fare_category": "adult_card_fare"
        }
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    # Check structure
    assert "driving" in data, "Response should have 'driving' key"
    assert "public_transport" in data, "Response should have 'public_transport' key"
    
    # Check driving metrics
    driving = data["driving"]
    assert "fuel_cost_sgd" in driving
    assert "total_cost" in driving
    assert "erp_charges" in driving
    assert "co2_emissions_kg" in driving
    assert driving["total_cost"] > 0, "Should have fuel cost"
    
    # Check public transport metrics
    pt = data["public_transport"]
    assert "total_fare" in pt
    assert "mrt_fare" in pt
    assert "bus_fare" in pt
    assert "segments" in pt
    
    # The NTU route should have non-zero fare (MRT portions)
    assert pt["total_fare"] > 0, "Total fare should be greater than 0"
    assert pt["mrt_fare"] > 0, "MRT fare should be greater than 0"
    
    # Bus fare should be 0 because campus shuttle is free
    assert pt["bus_fare"] == 0.0, "Bus fare should be 0 (campus shuttle is free)"
    
    # Should have segments
    assert len(pt["segments"]) > 0, "Should have transit segments"
    
    print("PASSED: Compare endpoint returns correct structure")
    print(f"   Total Fare: ${pt['total_fare']:.2f}")
    print(f"   MRT Fare: ${pt['mrt_fare']:.2f}")
    print(f"   Bus Fare: ${pt['bus_fare']:.2f}")
    print(f"   Segments: {len(pt['segments'])}")
    
    return True


def test_compare_endpoint_campus_shuttle_free():
    """Test that campus shuttles are correctly identified as free"""
    print("\n" + "="*80)
    print("TEST 2: Campus shuttles are free")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 37.0,
            "route_polyline": "test",
            "origin": "1.3483,103.6831",  # NTU (has campus shuttle)
            "destination": "1.3521,103.8198",
            "fare_category": "adult_card_fare"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    pt = data["public_transport"]
    segments = pt.get("segments", [])
    
    # Find campus shuttle segment
    campus_shuttle_segments = [s for s in segments if s.get("transport_type") == "Campus Shuttle"]
    
    assert len(campus_shuttle_segments) > 0, "Should have at least one campus shuttle segment"
    
    # Check that all campus shuttles are free
    for segment in campus_shuttle_segments:
        assert segment["fare"] == 0.0, f"Campus shuttle {segment['line_name']} should be free"
        assert "Campus Rider" in segment["line_name"], "Should be identified as Campus Rider"
    
    print("PASSED: Campus shuttles are free")
    for seg in campus_shuttle_segments:
        print(f"   {seg['line_name']}: ${seg['fare']:.2f}")
    
    return True


def test_compare_endpoint_invalid_coordinates():
    """Test error handling for invalid coordinates"""
    print("\n" + "="*80)
    print("TEST 3: Invalid coordinates return error")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 10.0,
            "route_polyline": "test",
            "origin": "invalid,coordinates",
            "destination": "1.3521,103.8198",
            "fare_category": "adult_card_fare"
        }
    )
    
    assert response.status_code == 422, f"Should return 422 for invalid coordinates, got {response.status_code}"
    
    print("PASSED: Invalid coordinates return 422 error")
    
    return True


def test_compare_endpoint_zero_distance():
    """Test error handling for zero distance"""
    print("\n" + "="*80)
    print("TEST 4: Zero distance returns error")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 0.0,
            "route_polyline": "test",
            "origin": "1.3483,103.6831",
            "destination": "1.3521,103.8198",
            "fare_category": "adult_card_fare"
        }
    )
    
    assert response.status_code == 422, f"Should return 422 for zero distance, got {response.status_code}"
    
    print("PASSED: Zero distance returns 422 error")
    
    return True


def test_compare_endpoint_fare_categories():
    """Test different fare categories"""
    print("\n" + "="*80)
    print("TEST 5: Different fare categories work")
    print("="*80)
    
    # Test adult fare
    adult_response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 20.0,
            "route_polyline": "test",
            "origin": "1.3521,103.8198",
            "destination": "1.2897,103.8501",
            "fare_category": "adult_card_fare"
        }
    )
    
    # Test senior fare
    senior_response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 20.0,
            "route_polyline": "test",
            "origin": "1.3521,103.8198",
            "destination": "1.2897,103.8501",
            "fare_category": "senior_card_fare"
        }
    )
    
    assert adult_response.status_code == 200, f"Adult request failed with {adult_response.status_code}"
    assert senior_response.status_code == 200, f"Senior request failed with {senior_response.status_code}"
    
    adult_data = adult_response.json()
    senior_data = senior_response.json()
    
    adult_fare = adult_data["public_transport"]["total_fare"]
    senior_fare = senior_data["public_transport"]["total_fare"]
    
    # Senior fare should be less than or equal to adult fare
    if adult_fare > 0 and senior_fare > 0:
        assert senior_fare <= adult_fare, "Senior fare should be <= adult fare"
        
        print("PASSED: Different fare categories work")
        print(f"   Adult Fare: ${adult_fare:.2f}")
        print(f"   Senior Fare: ${senior_fare:.2f}")
    else:
        print("SKIPPED: No transit route available for this origin-destination pair")
    
    return True


def test_compare_endpoint_cost_displayed_in_frontend():
    """Test that cost field is properly populated for frontend display"""
    print("\n" + "="*80)
    print("TEST 6: Cost field is populated for frontend ComparePage")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/metrics/compare",
        params={
            "distance_km": 37.0,
            "route_polyline": "test",
            "origin": "1.3483,103.6831",  # NTU
            "destination": "1.3521,103.8198",  # Paya Lebar
            "fare_category": "adult_card_fare"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    pt = data["public_transport"]
    
    # Frontend needs these fields
    assert "total_fare" in pt, "total_fare field must exist"
    assert isinstance(pt["total_fare"], (int, float)), "total_fare must be a number"
    assert pt["total_fare"] >= 0, "total_fare must be non-negative"
    
    print("PASSED: Cost field is properly populated")
    print(f"   Frontend can display: ${pt['total_fare']:.2f}")
    print(f"   Frontend receives total_fare: {pt['total_fare']} (type: {type(pt['total_fare']).__name__})")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("INTEGRATION TESTS: /metrics/compare endpoint")
    print("Testing public transport fare calculation and ComparePage integration")
    print("="*80)
    
    tests = [
        ("Basic Structure", test_compare_endpoint_with_public_transport),
        ("Campus Shuttle Free", test_compare_endpoint_campus_shuttle_free),
        ("Invalid Coordinates", test_compare_endpoint_invalid_coordinates),
        ("Zero Distance", test_compare_endpoint_zero_distance),
        ("Fare Categories", test_compare_endpoint_fare_categories),
        ("Frontend Integration", test_compare_endpoint_cost_displayed_in_frontend),
    ]
    
    passed = 0
    failed = 0
    errors = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\nFAILED: {e}")
        except Exception as e:
            errors += 1
            print(f"\nERROR: {e}")
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"WARNING: Errors: {errors}")
    print("="*80)
    
    if failed == 0 and errors == 0:
        print("\n ALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED - Please review the output above")
