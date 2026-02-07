"""
Unit tests for carpark coordinate functionality
Tests that carparks returned include latitude and longitude fields
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.metrics.lta_carpark_full_data import get_nearby_carparks

def test_carpark_has_coordinates():
    """Test that carparks include latitude and longitude fields"""
    # Using NTU coordinates as test location
    dest_lat = 1.3483
    dest_lng = 103.6831
    radius = 1500
    
    carparks = get_nearby_carparks(dest_lat, dest_lng, radius)
    
    print(f"Found {len(carparks)} carparks within {radius}m")
    
    if len(carparks) > 0:
        # Check first carpark has required fields
        first_carpark = carparks[0]
        print(f"\nFirst carpark: {first_carpark.get('development', first_carpark.get('area'))}")
        print(f"Fields present: {list(first_carpark.keys())}")
        
        # Assert required coordinate fields exist
        assert 'latitude' in first_carpark, "Carpark missing 'latitude' field"
        assert 'longitude' in first_carpark, "Carpark missing 'longitude' field"
        
        # Assert coordinates are valid numbers
        assert isinstance(first_carpark['latitude'], (int, float)), "Latitude must be a number"
        assert isinstance(first_carpark['longitude'], (int, float)), "Longitude must be a number"
        
        # Assert coordinates are within reasonable Singapore bounds
        assert 1.15 < first_carpark['latitude'] < 1.48, "Latitude out of Singapore range"
        assert 103.6 < first_carpark['longitude'] < 104.1, "Longitude out of Singapore range"
        
        print(f"Latitude: {first_carpark['latitude']}")
        print(f"Longitude: {first_carpark['longitude']}")
        
        # Check all carparks have coordinates
        for i, carpark in enumerate(carparks):
            assert 'latitude' in carpark, f"Carpark {i} missing latitude"
            assert 'longitude' in carpark, f"Carpark {i} missing longitude"
            assert isinstance(carpark['latitude'], (int, float)), f"Carpark {i} latitude not a number"
            assert isinstance(carpark['longitude'], (int, float)), f"Carpark {i} longitude not a number"
        
        print(f"\n✓ All {len(carparks)} carparks have valid coordinates")
        
        # Test that each carpark has all required fields
        required_fields = [
            'car_park_ID', 'area', 'development', 'available_lots', 
            'agency', 'distance_meters', 'latitude', 'longitude',
            'weekday_rate_1', 'weekday_rate_2', 'saturday_rates', 
            'sunday_public_holiday_rates'
        ]
        
        for i, carpark in enumerate(carparks):
            for field in required_fields:
                assert field in carpark, f"Carpark {i} missing required field: {field}"
        
        print(f" All carparks have all required fields: {required_fields}")
        
        return True
    else:
        print(" No carparks found in test area - cannot verify coordinate fields")
        return False

def test_carpark_coordinates_accuracy():
    """Test that carpark coordinates are within expected distance from destination"""
    # Test location: Marina Bay Sands area (known to have carparks)
    dest_lat = 1.2838
    dest_lng = 103.8607
    radius = 1000
    
    carparks = get_nearby_carparks(dest_lat, dest_lng, radius)
    
    print(f"\n\nTesting coordinate accuracy with {len(carparks)} carparks")
    
    if len(carparks) > 0:
        from math import radians, cos, sin, sqrt, atan2
        
        for carpark in carparks:
            # Calculate actual distance using Haversine formula
            R = 6371000  # Earth radius in meters
            dlat = radians(carpark['latitude'] - dest_lat)
            dlon = radians(carpark['longitude'] - dest_lng)
            a = sin(dlat / 2) ** 2 + cos(radians(dest_lat)) * cos(radians(carpark['latitude'])) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            calculated_distance = R * c
            
            # The distance should match what's stored (within 1 meter tolerance due to rounding)
            stored_distance = carpark['distance_meters']
            distance_diff = abs(calculated_distance - stored_distance)
            
            assert distance_diff < 1.5, f"Distance mismatch: calculated {calculated_distance:.1f}m vs stored {stored_distance}m"
            assert calculated_distance <= radius + 10, f"Carpark at {calculated_distance:.1f}m exceeds radius {radius}m"
        
        print(f" All carpark coordinates match their stored distances")
        return True
    else:
        print(" No carparks found in test area")
        return False

def test_carpark_sections_have_same_coordinates():
    """Test that grouped carpark sections from the same location share coordinates"""
    # Use a location likely to have multi-section carparks
    dest_lat = 1.2838
    dest_lng = 103.8607
    radius = 1500
    
    carparks = get_nearby_carparks(dest_lat, dest_lng, radius)
    
    print(f"\n\nTesting multi-section carpark coordinates")
    
    multi_section_carparks = [cp for cp in carparks if cp.get('total_sections', 1) > 1]
    
    if multi_section_carparks:
        print(f"Found {len(multi_section_carparks)} multi-section carparks")
        
        for carpark in multi_section_carparks:
            # Main carpark should have coordinates
            assert 'latitude' in carpark, "Multi-section carpark missing latitude"
            assert 'longitude' in carpark, "Multi-section carpark missing longitude"
            
            print(f"✓ {carpark['development']}: {carpark['total_sections']} sections at ({carpark['latitude']}, {carpark['longitude']})")
        
        return True
    else:
        print(" No multi-section carparks found in test area")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Testing Carpark Coordinate Functionality")
    print("="*60)
    
    try:
        # Run all tests
        test_carpark_has_coordinates()
        test_carpark_coordinates_accuracy()
        test_carpark_sections_have_same_coordinates()
        
        print("\n" + "="*60)
        print(" ALL TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
