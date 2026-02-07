"""
Demo: Camera Loading and Route Filtering
Shows how the system loads cameras and filters by route
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domain.camera_loader import get_camera_loader
from domain.geospatial_service import GeospatialService
from domain.route_models import Point, LineString

print("=" * 70)
print("CAMERA LOADING & ROUTE FILTERING DEMO")
print("=" * 70)

# 1. Load all cameras from JSON
print("\n[1] Loading cameras from JSON file...")
loader = get_camera_loader()
all_cameras = loader.load_cameras()
print(f"✓ Loaded {len(all_cameras)} cameras from train/data/cam_id_lat_lon.json")

# Show first few cameras
print("\nFirst 5 cameras:")
for cam in all_cameras[:5]:
    print(f"  - {cam.camera_id}: ({cam.latitude:.4f}, {cam.longitude:.4f})")

# 2. Define a sample route (Singapore: roughly Orchard to Marina Bay)
print("\n[2] Defining route...")
route = LineString([
    Point(1.3048, 103.8318),  # Orchard Road area
    Point(1.2950, 103.8580),  # City area
    Point(1.2806, 103.8611)   # Marina Bay area
])
print(f"✓ Route with {len(route.points)} points")
for i, p in enumerate(route.points):
    print(f"  Point {i+1}: ({p.latitude:.4f}, {p.longitude:.4f})")

# 3. Find cameras within 0.5km of route
print("\n[3] Finding cameras along route (within 500m)...")
geo_service = GeospatialService()
route_cameras = geo_service.find_cameras_along_route(
    route, all_cameras, search_radius_km=0.5
)

print(f"✓ Found {len(route_cameras)} cameras along route")
print(f"✓ Filtered from {len(all_cameras)} total cameras")
print(f"✓ Efficiency: Only using {len(route_cameras)/len(all_cameras)*100:.1f}% of cameras")

# 4. Show cameras found
print("\nCameras along route (sorted by position):")
for cam in route_cameras:
    print(f"  - Camera {cam.camera_id}")
    print(f"    Location: ({cam.latitude:.4f}, {cam.longitude:.4f})")
    print(f"    Distance from route: {cam.distance_to_route:.0f}m")
    print(f"    Position on route: {cam.position_on_route:.2f} (0=start, 1=end)")

# 5. Calculate route length
print("\n[4] Route analysis...")
route_length = geo_service.calculate_route_length(route)
print(f"✓ Total route length: {route_length:.2f} km")

# 6. Show benefit
print("\n[5] Why this is efficient:")
print(f"  • Only query {len(route_cameras)} cameras (not all {len(all_cameras)})")
print(f"  • Faster forecast retrieval from Redis/DB")
print(f"  • More accurate traffic analysis (only relevant cameras)")
print(f"  • Scales to any route without performance hit")

print("\n" + "=" * 70)
print("✓ Demo complete!")
print("=" * 70)
print("\nHow it works:")
print("1. Loads 90 cameras from static JSON file (one-time)")
print("2. Uses geometric algorithms to find cameras near route")
print("3. Only those cameras are queried for CI and forecasts")
print("4. Result: Fast, efficient, and accurate route optimization")
