"""
Seed sample user routes for testing.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

sample_routes = [
    {
        "user_id": 1,
        "title": "Morning Jog at Marina Bay",
        "description": "Scenic route along the waterfront with great views of the city skyline. Perfect for early morning runs!",
        "route_points": [
            {"latitude": 1.2830, "longitude": 103.8510, "order": 0},
            {"latitude": 1.2840, "longitude": 103.8520, "order": 1},
            {"latitude": 1.2850, "longitude": 103.8530, "order": 2},
            {"latitude": 1.2860, "longitude": 103.8540, "order": 3},
            {"latitude": 1.2870, "longitude": 103.8550, "order": 4}
        ],
        "transport_mode": "walking",
        "distance": 1500,
        "duration": 900,
        "is_public": True,
        "created_by": "morning_runner"
    },
    {
        "user_id": 1,
        "title": "East Coast Park Cycling Route",
        "description": "Popular cycling path along East Coast with beautiful beach views. Family-friendly and well-paved.",
        "route_points": [
            {"latitude": 1.3000, "longitude": 103.9000, "order": 0},
            {"latitude": 1.3020, "longitude": 103.9050, "order": 1},
            {"latitude": 1.3040, "longitude": 103.9100, "order": 2},
            {"latitude": 1.3060, "longitude": 103.9150, "order": 3}
        ],
        "transport_mode": "bicycling",
        "distance": 5000,
        "duration": 1200,
        "is_public": True,
        "created_by": "cyclist_pro"
    },
    {
        "user_id": 2,
        "title": "Scenic Drive to Sentosa",
        "description": "Beautiful coastal drive with minimal traffic during weekdays. Great for a relaxing drive with ocean views.",
        "route_points": [
            {"latitude": 1.2500, "longitude": 103.8200, "order": 0},
            {"latitude": 1.2550, "longitude": 103.8250, "order": 1},
            {"latitude": 1.2600, "longitude": 103.8300, "order": 2},
            {"latitude": 1.2650, "longitude": 103.8350, "order": 3}
        ],
        "transport_mode": "driving",
        "distance": 8000,
        "duration": 720,
        "is_public": True,
        "created_by": "driver123"
    },
    {
        "user_id": 2,
        "title": "Southern Ridges Trail",
        "description": "Nature walk connecting several parks with stunning canopy walkway. Moderately challenging but rewarding!",
        "route_points": [
            {"latitude": 1.2758, "longitude": 103.8115, "order": 0},
            {"latitude": 1.2770, "longitude": 103.8125, "order": 1},
            {"latitude": 1.2780, "longitude": 103.8140, "order": 2},
            {"latitude": 1.2790, "longitude": 103.8155, "order": 3},
            {"latitude": 1.2800, "longitude": 103.8170, "order": 4}
        ],
        "transport_mode": "walking",
        "distance": 3200,
        "duration": 2400,
        "is_public": True,
        "created_by": "nature_lover"
    },
    {
        "user_id": 1,
        "title": "Orchard Road Shopping Route",
        "description": "Walking tour of Orchard Road's best shopping malls with covered walkways. Rain or shine!",
        "route_points": [
            {"latitude": 1.3048, "longitude": 103.8318, "order": 0},
            {"latitude": 1.3038, "longitude": 103.8328, "order": 1},
            {"latitude": 1.3028, "longitude": 103.8338, "order": 2},
            {"latitude": 1.3018, "longitude": 103.8348, "order": 3}
        ],
        "transport_mode": "walking",
        "distance": 1800,
        "duration": 1080,
        "is_public": True,
        "created_by": "shopaholic88"
    }
]

def seed_routes():
    print("🌱 Seeding sample user routes...")
    
    created_count = 0
    for route in sample_routes:
        try:
            response = requests.post(
                f"{BASE_URL}/user-routes",
                json=route,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                created_count += 1
                data = response.json()
                print(f"✅ Created: {data['title']}")
            else:
                print(f"❌ Failed: {route['title']} - Status {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error creating {route['title']}: {str(e)}")
    
    print(f"\n🎉 Successfully created {created_count}/{len(sample_routes)} routes!")
    
    # Verify
    try:
        response = requests.get(f"{BASE_URL}/user-routes")
        if response.status_code == 200:
            routes = response.json()
            print(f"✅ Verification: {len(routes)} total routes in database")
    except Exception as e:
        print(f"⚠️  Could not verify: {str(e)}")

if __name__ == "__main__":
    seed_routes()
