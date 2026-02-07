"""
Test the compare endpoint to debug public transport fare calculation
"""
import requests
import json

# Test coordinates
origin = "1.3483,103.6831"  # NTU
destination = "1.3521,103.8198"  # Paya Lebar
distance_km = 37

url = f"http://localhost:8000/metrics/compare"
params = {
    "distance_km": distance_km,
    "route_polyline": "test",
    "origin": origin,
    "destination": destination,
    "fare_category": "adult_card_fare"
}

print("Testing /metrics/compare endpoint...")
print(f"URL: {url}")
print(f"Params: {json.dumps(params, indent=2)}")
print("="*80)

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print("\n✅ SUCCESS\n")
    print(json.dumps(data, indent=2))
    
    # Check public transport fare
    pt = data.get("public_transport", {})
    print("\n" + "="*80)
    print("PUBLIC TRANSPORT ANALYSIS:")
    print("="*80)
    print(f"Total Fare: ${pt.get('total_fare', 0):.2f}")
    print(f"MRT Fare: ${pt.get('mrt_fare', 0):.2f}")
    print(f"Bus Fare: ${pt.get('bus_fare', 0):.2f}")
    print(f"Number of segments: {len(pt.get('segments', []))}")
    
    if pt.get('total_fare', 0) > 0:
        print("\nPASS: Public transport fare is being calculated!")
        
        segments = pt.get('segments', [])
        print(f"\nSegments breakdown:")
        for i, seg in enumerate(segments, 1):
            print(f"\n  Segment {i}:")
            print(f"    Type: {seg.get('transport_type', 'N/A')}")
            print(f"    Line: {seg.get('line_name', 'N/A')}")
            print(f"    Distance: {seg.get('distance_km', 0)} km")
            print(f"    Fare: ${seg.get('fare', 0):.2f}")
            print(f"    From: {seg.get('departure_stop', 'N/A')}")
            print(f"    To: {seg.get('arrival_stop', 'N/A')}")
    else:
        print("\nFAIL: Public transport fare is $0.00")
        print("This means no segments were calculated.")
        
else:
    print(f"\nERROR: Status code {response.status_code}")
    print(response.text)
