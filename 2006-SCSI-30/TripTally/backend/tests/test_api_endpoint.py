"""
Quick API endpoint test to verify carpark coordinates are returned
"""
import requests
import json

def test_carpark_api_endpoint():
    print("Testing Carpark API Endpoint")
    print("="*60)
    
    # Test endpoint
    base_url = "http://localhost:8000"
    latitude = 1.2838
    longitude = 103.8607
    
    url = f"{base_url}/metrics/carparks?latitude={latitude}&longitude={longitude}"
    
    print(f"\nCalling: {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            carparks = response.json()
            print(f"Response Status: {response.status_code}")
            print(f"Found {len(carparks)} carparks")
            
            if len(carparks) > 0:
                first_carpark = carparks[0]
                print(f"\nFirst carpark: {first_carpark.get('development', first_carpark.get('area'))}")
                print(f"   Fields present: {list(first_carpark.keys())}")
                
                # Check for coordinates
                if 'latitude' in first_carpark and 'longitude' in first_carpark:
                    print(f"\nLatitude: {first_carpark['latitude']}")
                    print(f"Longitude: {first_carpark['longitude']}")
                    print(f"Distance: {first_carpark.get('distance_meters')}m")
                    print(f"Available Lots: {first_carpark.get('available_lots')}")
                    
                    print("\n" + "="*60)
                    print("API ENDPOINT TEST PASSED")
                    print("="*60)
                    return True
                else:
                    print("\n ERROR: Coordinates not found in response")
                    return False
            else:
                print("\nNo carparks returned (might be outside coverage area)")
                return True
        else:
            print(f"\nERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\nWARNING: Cannot connect to backend server")
        print("   Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    test_carpark_api_endpoint()
