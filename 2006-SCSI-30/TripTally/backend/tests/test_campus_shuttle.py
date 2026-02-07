"""
Test to verify campus shuttle buses are correctly identified as free
"""
import sys
sys.path.insert(0, '/Users/ethanchong/Documents/GitHub/triptally/TripTally/backend')

from app.metrics.get_pt_metrics import calculate_route_fares_from_steps

# Test with the NTU campus bus route
route_data_with_campus_bus = {
    "steps": [
        {
            "travel_mode": "WALKING",
            "distance_text": "0.3 km",
            "duration_text": "4 mins"
        },
        {
            "travel_mode": "TRANSIT",
            "distance_text": "2.3 km",
            "duration_text": "10 mins",
            "transit_details": {
                "headsign": "650B HDB",
                "num_stops": 1,
                "line_name": "Campus Rider - Green (CR)",
                "line_short_name": "Rider Green",
                "vehicle_type": "BUS",
                "vehicle_name": "Bus",
                "departure_stop": "Opp Hall 2",
                "arrival_stop": "650B HDB",
                "departure_time_text": "11:45 AM",
                "arrival_time_text": "11:55 AM"
            }
        },
        {
            "travel_mode": "WALKING",
            "distance_text": "87 m",
            "duration_text": "1 min"
        },
        {
            "travel_mode": "TRANSIT",
            "distance_text": "18.7 km",
            "duration_text": "27 mins",
            "transit_details": {
                "headsign": "Pasir Ris",
                "num_stops": 12,
                "line_name": "East West Line",
                "line_short_name": "EW",
                "vehicle_type": "SUBWAY",
                "vehicle_name": "Subway",
                "departure_stop": "Pioneer",
                "arrival_stop": "Outram Park",
                "departure_time_text": "12:03 PM",
                "arrival_time_text": "12:30 PM"
            }
        },
        {
            "travel_mode": "WALKING",
            "distance_text": "29 m",
            "duration_text": "1 min"
        },
        {
            "travel_mode": "TRANSIT",
            "distance_text": "12.8 km",
            "duration_text": "20 mins",
            "transit_details": {
                "headsign": "Woodlands North",
                "num_stops": 9,
                "line_name": "Thomson East Coast Line",
                "line_short_name": "TE",
                "vehicle_type": "SUBWAY",
                "vehicle_name": "Subway",
                "departure_stop": "Outram Park",
                "arrival_stop": "Bright Hill",
                "departure_time_text": "12:37 PM",
                "arrival_time_text": "12:57 PM"
            }
        },
        {
            "travel_mode": "WALKING",
            "distance_text": "2.7 km",
            "duration_text": "41 mins"
        }
    ]
}

print("Testing campus shuttle bus detection...")
print("="*80)

result = calculate_route_fares_from_steps(route_data_with_campus_bus)

print(f"\nTotal Fare: ${result['total_fare']:.2f}")
print(f"MRT Fare: ${result['mrt_fare']:.2f}")
print(f"Bus Fare: ${result['bus_fare']:.2f}")
print(f"\nRoute Details:")
print("-"*80)

for i, detail in enumerate(result['route_details'], 1):
    print(f"\nSegment {i}:")
    print(f"  Transport Type: {detail['transport_type']}")
    print(f"  Line: {detail['line_name']}")
    print(f"  Distance: {detail['distance_km']} km")
    print(f"  Fare: ${detail['fare']:.2f}")
    print(f"  From: {detail['departure_stop']}")
    print(f"  To: {detail['arrival_stop']}")

print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)

# Check if campus shuttle is free
campus_shuttle_segment = result['route_details'][0]
if campus_shuttle_segment['transport_type'] == 'Campus Shuttle' and campus_shuttle_segment['fare'] == 0.0:
    print("PASS: Campus shuttle correctly identified as free")
else:
    print(f"FAIL: Campus shuttle not free. Type: {campus_shuttle_segment['transport_type']}, Fare: ${campus_shuttle_segment['fare']}")

# Check if bus fare is $0 (since only bus is campus shuttle)
if result['bus_fare'] == 0.0:
    print("PASS: Total bus fare is $0.00 (campus shuttle only)")
else:
    print(f"FAIL: Total bus fare should be $0.00 but got ${result['bus_fare']:.2f}")

# Check total fare equals MRT fare only
expected_total = result['mrt_fare']
if abs(result['total_fare'] - expected_total) < 0.01:
    print(f"PASS: Total fare (${result['total_fare']:.2f}) equals MRT fare only")
else:
    print(f"FAIL: Total fare should be ${expected_total:.2f} but got ${result['total_fare']:.2f}")

print("\nAll tests completed!")
