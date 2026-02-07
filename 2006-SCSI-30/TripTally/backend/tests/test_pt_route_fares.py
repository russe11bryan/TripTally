"""
Unit tests for calculate_route_fares_from_steps function
Tests the new public transport fare calculation from Google Maps route data
"""

import sys
import os

# Add the metrics directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'metrics'))

from get_pt_metrics import calculate_route_fares_from_steps

def test_bus_only_route():
    """Test a route with only bus transit (Bus 166)"""
    print("\n=== Test 1: Bus Only Route (Bus 166) ===")
    
    # Sample route data with Bus 166 (from actual Google Maps API response)
    route_data = {
        "steps": [
            {
                "instruction": "Walk to Aft Windsor Pk Rd",
                "travel_mode": "WALKING",
                "distance_text": "2.2 km",
                "duration_text": "30 mins"
            },
            {
                "instruction": "Bus towards Clementi",
                "travel_mode": "TRANSIT",
                "distance_text": "9.3 km",
                "duration_text": "34 mins",
                "transit_details": {
                    "headsign": "Clementi",
                    "num_stops": 23,
                    "line_name": "166",
                    "vehicle_type": "BUS",
                    "vehicle_name": "Bus",
                    "departure_stop": "Aft Windsor Pk Rd",
                    "arrival_stop": "Opp The Treasury",
                    "departure_time_text": "11:36 AM",
                    "arrival_time_text": "12:10 PM",
                    "line_color": "#55dd33",
                    "line_text_color": "#000000"
                }
            },
            {
                "instruction": "Walk to destination",
                "travel_mode": "WALKING",
                "distance_text": "0.2 km",
                "duration_text": "3 mins"
            }
        ]
    }
    
    result = calculate_route_fares_from_steps(route_data)
    
    print(f"Total Fare: ${result['total_fare']:.2f}")
    print(f"Bus Fare: ${result['bus_fare']:.2f}")
    print(f"MRT Fare: ${result['mrt_fare']:.2f}")
    print(f"Number of transit segments: {len(result['route_details'])}")
    
    for i, detail in enumerate(result['route_details'], 1):
        print(f"\nSegment {i}:")
        print(f"  Type: {detail['transport_type']}")
        print(f"  Line: {detail['line_name']}")
        print(f"  Distance: {detail['distance_km']} km")
        print(f"  Fare: ${detail['fare']:.2f}")
        print(f"  From: {detail['departure_stop']}")
        print(f"  To: {detail['arrival_stop']}")
        print(f"  Departure: {detail['departure_time']}")
        print(f"  Arrival: {detail['arrival_time']}")
    
    # Assertions
    assert result['bus_fare'] > 0, "Bus fare should be greater than 0"
    assert result['mrt_fare'] == 0, "MRT fare should be 0 for bus-only route"
    assert result['total_fare'] == result['bus_fare'], "Total fare should equal bus fare"
    assert len(result['route_details']) == 1, "Should have 1 transit segment"
    assert result['route_details'][0]['line_name'] == "166", "Line name should be 166"
    
    print("\nTest 1 PASSED")
    return result

def test_mrt_and_bus_route():
    """Test a route with both MRT and bus transit"""
    print("\n=== Test 2: Mixed Route (MRT + Bus) ===")
    
    route_data = {
        "steps": [
            {
                "instruction": "Walk to MRT station",
                "travel_mode": "WALKING",
                "distance_text": "0.5 km",
                "duration_text": "7 mins"
            },
            {
                "instruction": "Subway towards Marina Bay",
                "travel_mode": "TRANSIT",
                "distance_text": "15.0 km",
                "duration_text": "25 mins",
                "transit_details": {
                    "headsign": "Marina Bay",
                    "num_stops": 10,
                    "line_name": "North South Line",
                    "vehicle_type": "SUBWAY",
                    "vehicle_name": "Metro",
                    "departure_stop": "Novena",
                    "arrival_stop": "Raffles Place",
                    "departure_time_text": "10:00 AM",
                    "arrival_time_text": "10:25 AM",
                    "line_color": "#D42E12",
                    "line_text_color": "#FFFFFF"
                }
            },
            {
                "instruction": "Walk to bus stop",
                "travel_mode": "WALKING",
                "distance_text": "0.3 km",
                "duration_text": "4 mins"
            },
            {
                "instruction": "Bus towards Changi",
                "travel_mode": "TRANSIT",
                "distance_text": "5.2 km",
                "duration_text": "15 mins",
                "transit_details": {
                    "headsign": "Changi",
                    "num_stops": 8,
                    "line_name": "36",
                    "vehicle_type": "BUS",
                    "vehicle_name": "Bus",
                    "departure_stop": "Raffles Place",
                    "arrival_stop": "Marina Bay",
                    "departure_time_text": "10:35 AM",
                    "arrival_time_text": "10:50 AM"
                }
            },
            {
                "instruction": "Walk to destination",
                "travel_mode": "WALKING",
                "distance_text": "0.1 km",
                "duration_text": "2 mins"
            }
        ]
    }
    
    result = calculate_route_fares_from_steps(route_data)
    
    print(f"Total Fare: ${result['total_fare']:.2f}")
    print(f"Bus Fare: ${result['bus_fare']:.2f}")
    print(f"MRT Fare: ${result['mrt_fare']:.2f}")
    print(f"Number of transit segments: {len(result['route_details'])}")
    
    for i, detail in enumerate(result['route_details'], 1):
        print(f"\nSegment {i}:")
        print(f"  Type: {detail['transport_type']}")
        print(f"  Line: {detail['line_name']}")
        print(f"  Distance: {detail['distance_km']} km")
        print(f"  Fare: ${detail['fare']:.2f}")
        print(f"  From: {detail['departure_stop']}")
        print(f"  To: {detail['arrival_stop']}")
    
    # Assertions
    assert result['bus_fare'] > 0, "Bus fare should be greater than 0"
    assert result['mrt_fare'] > 0, "MRT fare should be greater than 0"
    assert result['total_fare'] == result['bus_fare'] + result['mrt_fare'], "Total fare should equal bus + MRT fare"
    assert len(result['route_details']) == 2, "Should have 2 transit segments"
    
    print("\nTest 2 PASSED")
    return result

def test_walking_only_route():
    """Test a route with only walking (no transit)"""
    print("\n=== Test 3: Walking Only Route ===")
    
    route_data = {
        "steps": [
            {
                "instruction": "Walk to destination",
                "travel_mode": "WALKING",
                "distance_text": "1.5 km",
                "duration_text": "20 mins"
            }
        ]
    }
    
    result = calculate_route_fares_from_steps(route_data)
    
    print(f"Total Fare: ${result['total_fare']:.2f}")
    print(f"Bus Fare: ${result['bus_fare']:.2f}")
    print(f"MRT Fare: ${result['mrt_fare']:.2f}")
    print(f"Number of transit segments: {len(result['route_details'])}")
    
    # Assertions
    assert result['total_fare'] == 0, "Total fare should be 0 for walking-only route"
    assert result['bus_fare'] == 0, "Bus fare should be 0"
    assert result['mrt_fare'] == 0, "MRT fare should be 0"
    assert len(result['route_details']) == 0, "Should have 0 transit segments"
    
    print("\nTest 3 PASSED")
    return result

def test_with_custom_fare_category():
    """Test with different fare category (senior card fare)"""
    print("\n=== Test 4: Custom Fare Category (Senior) ===")
    
    route_data = {
        "steps": [
            {
                "instruction": "Bus towards destination",
                "travel_mode": "TRANSIT",
                "distance_text": "8.0 km",
                "duration_text": "20 mins",
                "transit_details": {
                    "line_name": "170",
                    "vehicle_type": "BUS",
                    "departure_stop": "Start",
                    "arrival_stop": "End",
                    "departure_time_text": "9:00 AM",
                    "arrival_time_text": "9:20 AM"
                }
            }
        ]
    }
    
    # Test with adult fare
    result_adult = calculate_route_fares_from_steps(route_data, fare_category="adult_card_fare")
    print(f"Adult Card Fare: ${result_adult['total_fare']:.2f}")
    
    # Test with senior fare
    result_senior = calculate_route_fares_from_steps(route_data, fare_category="senior_card_fare")
    print(f"Senior Card Fare: ${result_senior['total_fare']:.2f}")
    
    # Senior fare should be less than adult fare
    assert result_senior['total_fare'] < result_adult['total_fare'], "Senior fare should be less than adult fare"
    
    print("\nTest 4 PASSED")
    return result_adult, result_senior

def test_express_bus():
    """Test with express bus"""
    print("\n=== Test 5: Express Bus ===")
    
    route_data = {
        "steps": [
            {
                "instruction": "Bus towards destination",
                "travel_mode": "TRANSIT",
                "distance_text": "25.0 km",
                "duration_text": "45 mins",
                "transit_details": {
                    "line_name": "502",  # Express bus
                    "vehicle_type": "BUS",
                    "departure_stop": "Jurong",
                    "arrival_stop": "City",
                    "departure_time_text": "7:00 AM",
                    "arrival_time_text": "7:45 AM"
                }
            }
        ]
    }
    
    result = calculate_route_fares_from_steps(route_data)
    
    print(f"Express Bus Fare: ${result['total_fare']:.2f}")
    print(f"Distance: {result['route_details'][0]['distance_km']} km")
    
    assert result['bus_fare'] > 0, "Express bus fare should be greater than 0"
    assert result['route_details'][0]['line_name'] == "502", "Line name should be 502"
    
    print("\nTest 5 PASSED")
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("Testing calculate_route_fares_from_steps()")
    print("=" * 60)
    
    try:
        # Run all tests
        test_bus_only_route()
        test_mrt_and_bus_route()
        test_walking_only_route()
        test_with_custom_fare_category()
        test_express_bus()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
