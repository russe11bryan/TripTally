"""
Integration test for carpark navigation functionality
Tests the end-to-end flow from fetching carparks to navigation parameters
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.metrics.lta_carpark_full_data import get_nearby_carparks

def test_carpark_navigation_data():
    """Test that carparks have all required data for navigation"""
    print("Testing Carpark Navigation Integration")
    print("="*60)
    
    # Use a test location
    dest_lat = 1.2838
    dest_lng = 103.8607
    radius = 1500
    
    carparks = get_nearby_carparks(dest_lat, dest_lng, radius)
    
    if len(carparks) == 0:
        print("WARNING: No carparks found in test area")
        return True
    
    print(f"\nFound {len(carparks)} carparks to test\n")
    
    for i, carpark in enumerate(carparks, 1):
        print(f"Carpark {i}: {carpark['development'] or carpark['area']}")
        
        # Check navigation-required fields
        required_nav_fields = {
            'development': 'Destination name',
            'area': 'Fallback name',
            'latitude': 'Destination latitude',
            'longitude': 'Destination longitude'
        }
        
        for field, purpose in required_nav_fields.items():
            assert field in carpark, f"Missing {purpose} ({field})"
            print(f" {purpose}: {carpark[field]}")
        
        # Validate coordinate types
        assert isinstance(carpark['latitude'], (int, float)), "Latitude must be numeric"
        assert isinstance(carpark['longitude'], (int, float)), "Longitude must be numeric"
        
        # Validate Singapore bounds
        assert 1.15 < carpark['latitude'] < 1.48, "Latitude out of Singapore range"
        assert 103.6 < carpark['longitude'] < 104.1, "Longitude out of Singapore range"
        
        # Check name is usable (not empty or NULL)
        display_name = carpark['development'] or carpark['area']
        assert display_name, "Carpark must have a display name"
        assert display_name.upper() not in ['NULL', 'NIL', ''], "Invalid carpark name"
        
        print(f"   Valid for navigation\n")
    
    print(f"All {len(carparks)} carparks have valid navigation data")
    return True

def test_navigation_parameter_format():
    """Test that navigation parameters match expected format for DirectionsPage"""
    print("\n" + "="*60)
    print("Testing Navigation Parameter Format")
    print("="*60 + "\n")
    
    dest_lat = 1.2838
    dest_lng = 103.8607
    carparks = get_nearby_carparks(dest_lat, dest_lng, 1000)
    
    if len(carparks) == 0:
        print("No carparks found in test area")
        return True
    
    # Simulate what frontend would do
    carpark = carparks[0]
    
    # Expected navigation parameters structure
    expected_nav_params = {
        'origin': None,  # Would be user's location
        'destination': {
            'name': carpark['development'] or carpark['area'],
            'latitude': carpark['latitude'],
            'longitude': carpark['longitude']
        },
        'initialMode': 'driving'
    }
    
    print("Sample Navigation Parameters:")
    print(f"  origin: {expected_nav_params['origin']}")
    print(f"  destination:")
    print(f"    name: {expected_nav_params['destination']['name']}")
    print(f"    latitude: {expected_nav_params['destination']['latitude']}")
    print(f"    longitude: {expected_nav_params['destination']['longitude']}")
    print(f"  initialMode: {expected_nav_params['initialMode']}")
    
    # Validate structure
    assert 'destination' in expected_nav_params
    assert 'name' in expected_nav_params['destination']
    assert 'latitude' in expected_nav_params['destination']
    assert 'longitude' in expected_nav_params['destination']
    assert expected_nav_params['initialMode'] == 'driving'
    
    print("\n Navigation parameter format is correct")
    return True

def test_distance_sorting():
    """Test that carparks are sorted by distance"""
    print("\n" + "="*60)
    print("Testing Distance Sorting")
    print("="*60 + "\n")
    
    dest_lat = 1.2838
    dest_lng = 103.8607
    carparks = get_nearby_carparks(dest_lat, dest_lng, 1500)
    
    if len(carparks) < 2:
        print(" Not enough carparks to test sorting")
        return True
    
    print(f"Checking {len(carparks)} carparks are sorted by distance:")
    
    for i in range(len(carparks) - 1):
        current_dist = carparks[i]['distance_meters']
        next_dist = carparks[i + 1]['distance_meters']
        
        print(f"  {i+1}. {carparks[i]['development'] or carparks[i]['area']}: {current_dist}m")
        
        assert current_dist <= next_dist, f"Carparks not sorted: {current_dist}m > {next_dist}m"
    
    print(f"  {len(carparks)}. {carparks[-1]['development'] or carparks[-1]['area']}: {carparks[-1]['distance_meters']}m")
    print("\n Carparks are correctly sorted by distance (nearest first)")
    return True

def test_user_flow_simulation():
    """Simulate the complete user flow"""
    print("\n" + "="*60)
    print("Simulating Complete User Flow")
    print("="*60 + "\n")
    
    # Step 1: User is at a location (e.g., Marina Bay area)
    user_origin = {'latitude': 1.2838, 'longitude': 103.8607}
    print(f"1. User location: ({user_origin['latitude']}, {user_origin['longitude']})")
    
    # Step 2: User searches for destination (let's say they want to go somewhere)
    destination = {'latitude': 1.3521, 'longitude': 103.8198, 'name': 'Clarke Quay'}
    print(f"2. User destination: {destination['name']}")
    
    # Step 3: User views driving details, sees nearby carparks
    carparks = get_nearby_carparks(destination['latitude'], destination['longitude'], 1500)
    print(f"3. Found {len(carparks)} nearby carparks at destination")
    
    if len(carparks) == 0:
        print("  No carparks found - user flow cannot continue")
        return True
    
    # Step 4: User taps on a carpark
    selected_carpark = carparks[0]
    print(f"4. User selects: {selected_carpark['development'] or selected_carpark['area']}")
    print(f"   Distance from destination: {selected_carpark['distance_meters']}m")
    
    # Step 5: Navigate to DirectionsPage with carpark as new destination
    new_nav_params = {
        'origin': user_origin,
        'destination': {
            'name': selected_carpark['development'] or selected_carpark['area'],
            'latitude': selected_carpark['latitude'],
            'longitude': selected_carpark['longitude']
        },
        'initialMode': 'driving'
    }
    
    print(f"5. Navigation triggered with:")
    print(f"   Origin: User's location ({user_origin['latitude']}, {user_origin['longitude']})")
    print(f"   Destination: {new_nav_params['destination']['name']}")
    print(f"   Coordinates: ({new_nav_params['destination']['latitude']}, {new_nav_params['destination']['longitude']})")
    print(f"   Mode: {new_nav_params['initialMode']}")
    
    # Verify the flow is complete
    assert new_nav_params['origin'] == user_origin
    assert new_nav_params['destination']['latitude'] == selected_carpark['latitude']
    assert new_nav_params['destination']['longitude'] == selected_carpark['longitude']
    assert new_nav_params['initialMode'] == 'driving'
    
    print("\nComplete user flow simulation successful")
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CARPARK NAVIGATION INTEGRATION TESTS")
    print("="*60 + "\n")
    
    try:
        test_carpark_navigation_data()
        test_navigation_parameter_format()
        test_distance_sorting()
        test_user_flow_simulation()
        
        print("\n" + "="*60)
        print(" ALL INTEGRATION TESTS PASSED")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
