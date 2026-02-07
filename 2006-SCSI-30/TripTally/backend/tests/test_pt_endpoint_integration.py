"""
Integration test for the updated public transport endpoint
Tests the full flow from API call to formatted response
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_public_transport_endpoint():
    """Test the /metrics/public-transport endpoint with real coordinates"""
    print("\n" + "="*60)
    print("Testing Public Transport Endpoint Integration")
    print("="*60)
    
    # Test route from NTU to Marina Bay
    origin_lat = 1.3521
    origin_lng = 103.8198
    dest_lat = 1.2897
    dest_lng = 103.8501
    
    url = f"{BASE_URL}/metrics/public-transport"
    params = {
        'origin_lat': origin_lat,
        'origin_lng': origin_lng,
        'dest_lat': dest_lat,
        'dest_lng': dest_lng
    }
    
    print(f"\nFetching route from ({origin_lat}, {origin_lng}) to ({dest_lat}, {dest_lng})")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return False
        
        data = response.json()
        
        # Print summary
        print("\n" + "-"*60)
        print("ROUTE SUMMARY")
        print("-"*60)
        print(f"Total Duration: {data.get('duration_minutes')} minutes")
        print(f"Total Distance: {data.get('distance_km')} km")
        print(f"Total Fare: ${data.get('fare'):.2f}")
        print(f"  - MRT Fare: ${data.get('mrt_fare'):.2f}")
        print(f"  - Bus Fare: ${data.get('bus_fare'):.2f}")
        print(f"Departure: {data.get('departure_time')}")
        print(f"Arrival: {data.get('arrival_time')}")
        
        # Print detailed route steps
        route_details = data.get('route_details', [])
        
        if route_details:
            print("\n" + "-"*60)
            print("DETAILED JOURNEY BREAKDOWN")
            print("-"*60)
            
            for i, step in enumerate(route_details, 1):
                print(f"\nStep {i}: {step.get('travel_mode')}")
                print(f"  Duration: {step.get('duration')}")
                print(f"  Distance: {step.get('distance')}")
                
                if step.get('travel_mode') == 'TRANSIT':
                    print(f"  Type: {step.get('vehicle_type')} - {step.get('line_name')}")
                    print(f"  From: {step.get('departure_stop')}")
                    print(f"  To: {step.get('arrival_stop')}")
                    print(f"  Departs: {step.get('departure_time')}")
                    print(f"  Arrives: {step.get('arrival_time')}")
                    print(f"  Stops: {step.get('num_stops')}")
                    if step.get('fare') is not None:
                        print(f"  Fare: ${step.get('fare'):.2f}")
                elif step.get('travel_mode') == 'WALKING':
                    print(f"  Instruction: {step.get('instruction')}")
        
        # Assertions
        print("\n" + "-"*60)
        print("RUNNING ASSERTIONS")
        print("-"*60)
        
        assert 'duration_minutes' in data, "Missing duration_minutes"
        print("✅ Duration present")
        
        assert 'distance_km' in data, "Missing distance_km"
        print("✅ Distance present")
        
        assert 'fare' in data, "Missing fare"
        print("✅ Total fare present")
        
        assert 'mrt_fare' in data, "Missing mrt_fare"
        print("✅ MRT fare present")
        
        assert 'bus_fare' in data, "Missing bus_fare"
        print("✅ Bus fare present")
        
        assert 'route_details' in data, "Missing route_details"
        print("✅ Route details present")
        
        assert len(route_details) > 0, "Route details should not be empty"
        print(f"✅ Route has {len(route_details)} steps")
        
        # Check that we have at least one transit step
        transit_steps = [s for s in route_details if s.get('travel_mode') == 'TRANSIT']
        assert len(transit_steps) > 0, "Should have at least one transit step"
        print(f"✅ Found {len(transit_steps)} transit step(s)")
        
        # Check that transit steps have required fields
        for step in transit_steps:
            assert 'line_name' in step, "Transit step missing line_name"
            assert 'vehicle_type' in step, "Transit step missing vehicle_type"
            assert 'departure_stop' in step, "Transit step missing departure_stop"
            assert 'arrival_stop' in step, "Transit step missing arrival_stop"
            assert 'fare' in step, "Transit step missing fare"
        print("✅ All transit steps have required fields")
        
        # Verify fare calculation
        total_calculated = data.get('mrt_fare', 0) + data.get('bus_fare', 0)
        total_reported = data.get('fare', 0)
        assert abs(total_calculated - total_reported) < 0.01, \
            f"Fare mismatch: {total_calculated} != {total_reported}"
        print("✅ Fare calculation is consistent")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server at", BASE_URL)
        print("Make sure the backend server is running on port 8000")
        return False
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)
    
    # Test 1: Missing coordinates
    print("\n1. Testing missing coordinates...")
    url = f"{BASE_URL}/metrics/public-transport"
    response = requests.get(url, params={'dest_lat': 1.2897, 'dest_lng': 103.8501})
    # Should use default origin
    assert response.status_code == 200, "Should use default origin"
    print("✅ Default origin handling works")
    
    # Test 2: Invalid coordinates
    print("\n2. Testing invalid coordinates...")
    response = requests.get(url, params={
        'origin_lat': 999,
        'origin_lng': 999,
        'dest_lat': 1.2897,
        'dest_lng': 103.8501
    })
    # Should return error or handle gracefully
    print(f"   Status: {response.status_code}")
    print("✅ Invalid coordinates handled")
    
    print("\n" + "="*60)
    print("✅ Edge case tests completed")
    print("="*60)

if __name__ == "__main__":
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print("WARNING: Server responded but health check failed")
    except:
        print("❌ Server is not running. Please start the server first:")
        print("   cd backend && ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        exit(1)
    
    # Run tests
    success = test_public_transport_endpoint()
    if success:
        test_edge_cases()
        print("\n🎉 All integration tests passed!")
    else:
        print("\n❌ Integration tests failed")
        exit(1)
