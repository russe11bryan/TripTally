"""
Test script to verify Google Roads API is working.
Run this to check if the Roads API is enabled for your API key.
"""
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

async def test_roads_api():
    """Test Google Roads API with a location on a road in Singapore."""
    
    # Test location: Marina Bay Sands (on a road)
    test_lat = 1.2838
    test_lon = 103.8607
    
    # Test location 2: Middle of Singapore Strait (definitely NOT on a road - far from land)
    test_lat_water = 1.22
    test_lon_water = 103.75
    
    # Test location 3: Sentosa beach (on land but not on road)
    test_lat_beach = 1.2494
    test_lon_beach = 103.8303
    
    print(f"API Key: {GOOGLE_MAPS_API_KEY[:10]}...")
    print(f"\n Test 1: Location on road (Marina Bay area)")
    print(f"   Coordinates: {test_lat}, {test_lon}")
    
    url = "https://roads.googleapis.com/v1/snapToRoads"
    params = {
        "path": f"{test_lat},{test_lon}",
        "key": GOOGLE_MAPS_API_KEY,
        "interpolate": "false"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    SUCCESS!")
            print(f"   Response: {data}")
            
            if "snappedPoints" in data and len(data["snappedPoints"]) > 0:
                print(f"    Found {len(data['snappedPoints'])} snapped point(s) - NEAR A ROAD")
            else:
                print(f"    No snapped points - NOT NEAR A ROAD")
        else:
            print(f"    ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if "API_KEY_INVALID" in response.text:
                print(f"\n   WARNING: Your API key is invalid!")
            elif "PERMISSION_DENIED" in response.text or "Roads API" in response.text:
                print(f"\n   WARNING: Google Roads API is NOT enabled for your API key!")
                print(f"    Enable it at: https://console.cloud.google.com/apis/library/roads.googleapis.com")
    
    print(f"\n Test 2: Location far from roads (Singapore Strait)")
    print(f"   Coordinates: {test_lat_water}, {test_lon_water}")
    
    params2 = {
        "path": f"{test_lat_water},{test_lon_water}",
        "key": GOOGLE_MAPS_API_KEY,
        "interpolate": "false"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params2)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            
            if "snappedPoints" in data and len(data["snappedPoints"]) > 0:
                print(f"   WARNING: Found snapped point - checking distance...")
                snapped = data["snappedPoints"][0]
                
                # Calculate distance
                def calc_distance(lat1, lon1, lat2, lon2):
                    import math
                    R = 6371000
                    phi1 = math.radians(lat1)
                    phi2 = math.radians(lat2)
                    delta_phi = math.radians(lat2 - lat1)
                    delta_lambda = math.radians(lon2 - lon1)
                    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    return R * c
                
                distance = calc_distance(test_lat_water, test_lon_water, 
                                       snapped["location"]["latitude"], 
                                       snapped["location"]["longitude"])
                print(f"   Distance: {distance:.2f} meters")
                print(f"   {' Within 50m' if distance <= 50 else ' Beyond 50m - should reject'}")
            else:
                print(f"   No snapped points - correctly identifies non-road location")
    
    print(f"\nTest 3: Location on beach (land but no road)")
    print(f"   Coordinates: {test_lat_beach}, {test_lon_beach}")
    
    params3 = {
        "path": f"{test_lat_beach},{test_lon_beach}",
        "key": GOOGLE_MAPS_API_KEY,
        "interpolate": "false"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params3)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "snappedPoints" in data and len(data["snappedPoints"]) > 0:
                print(f"   Response: {data}")
                snapped = data["snappedPoints"][0]
                
                def calc_distance(lat1, lon1, lat2, lon2):
                    import math
                    R = 6371000
                    phi1 = math.radians(lat1)
                    phi2 = math.radians(lat2)
                    delta_phi = math.radians(lat2 - lat1)
                    delta_lambda = math.radians(lon2 - lon1)
                    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    return R * c
                
                distance = calc_distance(test_lat_beach, test_lon_beach, 
                                       snapped["location"]["latitude"], 
                                       snapped["location"]["longitude"])
                print(f"   Distance: {distance:.2f} meters")
                print(f"   {' Within 50m - allow' if distance <= 50 else '❌ Beyond 50m - should reject'}")
            else:
                print(f"    No snapped points")

if __name__ == "__main__":
    print(" Testing Google Roads API\n")
    asyncio.run(test_roads_api())
    print("\n Test complete!")
