#!/usr/bin/env python3
"""
Test script for transport metrics endpoints
Tests all the endpoints used by TransportDetailsPage
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

# Test coordinates (Lee Wee Nam Library at NTU)
DEST_LAT = 1.3010451
DEST_LNG = 103.8385792
ORIGIN_LAT = 1.3476541  # Somewhere in Singapore
ORIGIN_LNG = 103.6815300

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_result(test_name, success, data=None, error=None):
    """Print test result"""
    status = "PASS" if success else "FAIL"
    print(f"\n{status} - {test_name}")
    if success and data:
        print(json.dumps(data, indent=2))
    elif error:
        print(f"Error: {error}")

def test_driving_metrics():
    """Test driving metrics endpoint"""
    print_section("Testing Driving Metrics")
    
    url = f"{BASE_URL}/metrics/driving"
    params = {
        "origin_lat": ORIGIN_LAT,
        "origin_lng": ORIGIN_LNG,
        "dest_lat": DEST_LAT,
        "dest_lng": DEST_LNG
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Validate required fields
        required_fields = [
            "duration_minutes", "distance_km", "erp_charges", 
            "fuel_cost_sgd", "co2_emissions_kg", "departure_time", 
            "arrival_time", "traffic_conditions"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print_result("Driving Metrics", False, error=f"Missing fields: {missing_fields}")
            return False
        
        print_result("Driving Metrics", True, data)
        
        # Print summary
        print("\nSummary:")
        print(f"  Duration: {data.get('duration_minutes')} mins")
        print(f"  Distance: {data.get('distance_km')} km")
        print(f"  Fuel Cost: ${data.get('fuel_cost_sgd', 0):.2f}")
        print(f"  ERP Charges: ${data.get('erp_charges', 0):.2f}")
        print(f"  Total Cost: ${data.get('total_cost', 0):.2f}")
        print(f"  CO2 Emissions: {data.get('co2_emissions_kg', 0):.2f} kg")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_result("Driving Metrics", False, error=str(e))
        return False
    except Exception as e:
        print_result("Driving Metrics", False, error=f"Unexpected error: {str(e)}")
        return False

def test_public_transport_metrics():
    """Test public transport metrics endpoint"""
    print_section("Testing Public Transport Metrics")
    
    url = f"{BASE_URL}/metrics/public-transport"
    params = {
        "origin_lat": ORIGIN_LAT,
        "origin_lng": ORIGIN_LNG,
        "dest_lat": DEST_LAT,
        "dest_lng": DEST_LNG
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Validate required fields
        required_fields = ["duration_minutes", "distance_km", "fare", "departure_time", "arrival_time"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_result("Public Transport Metrics", False, error=f"Missing fields: {missing_fields}")
            return False
        
        print_result("Public Transport Metrics", True, data)
        
        # Print summary
        print("\nSummary:")
        print(f"  Duration: {data.get('duration_minutes')} mins")
        print(f"  Distance: {data.get('distance_km')} km")
        print(f"  Fare: ${data.get('fare', 0):.2f}")
        if 'mrt_fare' in data:
            print(f"  MRT Fare: ${data.get('mrt_fare', 0):.2f}")
        if 'bus_fare' in data:
            print(f"  Bus Fare: ${data.get('bus_fare', 0):.2f}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_result("Public Transport Metrics", False, error=str(e))
        return False
    except Exception as e:
        print_result("Public Transport Metrics", False, error=f"Unexpected error: {str(e)}")
        return False

def test_walking_metrics():
    """Test walking metrics endpoint"""
    print_section("Testing Walking Metrics")
    
    url = f"{BASE_URL}/metrics/walking"
    params = {
        "origin_lat": ORIGIN_LAT,
        "origin_lng": ORIGIN_LNG,
        "dest_lat": DEST_LAT,
        "dest_lng": DEST_LNG
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Validate required fields
        required_fields = ["duration_minutes", "distance_km", "calories", "departure_time", "arrival_time"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_result("Walking Metrics", False, error=f"Missing fields: {missing_fields}")
            return False
        
        print_result("Walking Metrics", True, data)
        
        # Print summary
        print("\nSummary:")
        print(f"  Duration: {data.get('duration_minutes')} mins")
        print(f"  Distance: {data.get('distance_km')} km")
        print(f"  Calories: {data.get('calories', 0)} kcal")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_result("Walking Metrics", False, error=str(e))
        return False
    except Exception as e:
        print_result("Walking Metrics", False, error=f"Unexpected error: {str(e)}")
        return False

def test_cycling_metrics():
    """Test cycling metrics endpoint"""
    print_section("Testing Cycling Metrics")
    
    url = f"{BASE_URL}/metrics/cycling"
    params = {
        "origin_lat": ORIGIN_LAT,
        "origin_lng": ORIGIN_LNG,
        "dest_lat": DEST_LAT,
        "dest_lng": DEST_LNG
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Validate required fields
        required_fields = ["duration_minutes", "distance_km", "calories", "departure_time", "arrival_time"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_result("Cycling Metrics", False, error=f"Missing fields: {missing_fields}")
            return False
        
        print_result("Cycling Metrics", True, data)
        
        # Print summary
        print("\nSummary:")
        print(f"  Duration: {data.get('duration_minutes')} mins")
        print(f"  Distance: {data.get('distance_km')} km")
        print(f"  Calories: {data.get('calories', 0)} kcal")
        if 'co2_saved' in data:
            print(f"  CO2 Saved: {data.get('co2_saved', 0)} kg")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_result("Cycling Metrics", False, error=str(e))
        return False
    except Exception as e:
        print_result("Cycling Metrics", False, error=f"Unexpected error: {str(e)}")
        return False

def test_carparks():
    """Test carparks endpoint"""
    print_section("Testing Carparks Endpoint")
    
    url = f"{BASE_URL}/metrics/carparks"
    params = {
        "latitude": DEST_LAT,
        "longitude": DEST_LNG,
        "radius_meters": 1500
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            print_result("Carparks", True, {"count": len(data), "carparks": data[:2]})  # Show first 2
            
            # Print summary
            print(f"\nFound {len(data)} carparks")
            if data:
                print("\nFirst carpark:")
                cp = data[0]
                print(f"  Name: {cp.get('development', cp.get('area', 'N/A'))}")
                print(f"  Available Lots: {cp.get('available_lots', 0)}")
                print(f"  Distance: {cp.get('distance_meters', 0)}m")
            
            return True
        else:
            print_result("Carparks", False, error="Expected list response")
            return False
        
    except requests.exceptions.RequestException as e:
        print_result("Carparks", False, error=str(e))
        return False
    except Exception as e:
        print_result("Carparks", False, error=f"Unexpected error: {str(e)}")
        return False

def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "healthy" or data.get("status") == "ok":
            print_result("Health Check", True, data)
            return True
        else:
            print_result("Health Check", False, error=f"Unexpected status: {data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result("Health Check", False, error=str(e))
        return False

def main():
    """Run all tests"""
    print("\n" + "-" * 20)
    print("  TRANSPORT METRICS API TEST SUITE")
    print("-" * 20)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test health check first
    results.append(("Health Check", test_health_check()))
    
    # Test all transport mode endpoints
    results.append(("Driving Metrics", test_driving_metrics()))
    results.append(("Public Transport Metrics", test_public_transport_metrics()))
    results.append(("Walking Metrics", test_walking_metrics()))
    results.append(("Cycling Metrics", test_cycling_metrics()))
    results.append(("Carparks", test_carparks()))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\nWARNING: {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
