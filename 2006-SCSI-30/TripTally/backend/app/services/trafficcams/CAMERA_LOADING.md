# Camera Loading Implementation

## Overview

The route optimization service now loads camera data from a static JSON file instead of querying the repository. This provides better performance and clearer separation of concerns.

## How It Works

### 1. Camera Data Source

**File**: `backend/app/services/trafficcams/train/data/cam_id_lat_lon.json`

**Format**:
```json
[
  {
    "cam_id": "1001",
    "lat": 1.29531332,
    "lon": 103.871146
  },
  ...
]
```

**Contains**: 90 Singapore traffic cameras with coordinates

### 2. Camera Loading Process

```
User Request (Route)
        │
        ▼
┌───────────────────┐
│ CameraDataLoader  │ ← Loads from JSON file (singleton)
│ load_cameras()    │
└────────┬──────────┘
         │ Returns ALL 90 cameras
         ▼
┌───────────────────────┐
│ GeospatialService     │
│ find_cameras_along_   │
│ route()               │
└────────┬──────────────┘
         │ Filters to cameras within search radius
         │ (e.g., 5 cameras out of 90)
         ▼
┌───────────────────────┐
│ RouteOptimizer        │
│ - Query forecasts     │
│   only for these      │
│   5 cameras           │
└───────────────────────┘
```

### 3. Efficiency Benefits

**Before** (querying repository):
- List all camera IDs from Redis/DB
- Get metadata for each camera (90 queries)
- Filter by route
- Get forecasts for filtered cameras

**After** (using JSON file):
- Load 90 cameras from JSON (cached in memory)
- Filter by route geometrically (no DB queries)
- Get forecasts only for filtered cameras (e.g., 5 queries)

**Result**: 
- 89% fewer database queries for metadata
- Faster response time
- Clearer data flow

## Code Structure

### CameraDataLoader (`domain/camera_loader.py`)

```python
class CameraDataLoader:
    """Loads camera data from JSON file"""
    
    DEFAULT_CAMERA_FILE = Path(__file__).parent.parent / "train" / "data" / "cam_id_lat_lon.json"
    
    def load_cameras(self) -> List[Camera]:
        """Load all cameras from JSON file"""
        # Loads and caches camera data
        
    def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """Get specific camera by ID"""
        
    def get_camera_ids(self) -> List[str]:
        """Get list of all camera IDs"""
```

**Features**:
- Singleton pattern (loads file once)
- In-memory caching
- Error handling for missing file/invalid JSON

### Integration with RouteOptimizer

```python
class RouteOptimizationService:
    def __init__(
        self,
        repository: DataRepository,
        geospatial_service: GeospatialService,
        camera_loader: CameraDataLoader  # NEW
    ):
        self.camera_loader = camera_loader
    
    def optimize_route(self, route, ...):
        # 1. Load ALL cameras from JSON
        all_cameras = self.camera_loader.load_cameras()
        
        # 2. Filter to cameras along route
        route_cameras = self.geo_service.find_cameras_along_route(
            route, all_cameras, search_radius_km
        )
        
        # 3. Query forecasts ONLY for filtered cameras
        for route_cam in route_cameras:
            forecast = self.repository.get_forecast(route_cam.camera_id)
            # ...
```

## Example Usage

### Direct Camera Loading

```python
from domain.camera_loader import get_camera_loader

# Get singleton loader
loader = get_camera_loader()

# Load all cameras
cameras = loader.load_cameras()
print(f"Loaded {len(cameras)} cameras")  # 90 cameras

# Get specific camera
cam = loader.get_camera_by_id("1001")
print(f"Camera 1001: {cam.latitude}, {cam.longitude}")
```

### Route Filtering Demo

```bash
# Run the demo
cd backend/app/services/trafficcams
python demo_camera_loading.py

# Output:
# Loaded 90 cameras from JSON
# Route with 3 points
# Found 5 cameras along route
# Efficiency: Only using 5.6% of cameras
```

## Performance Comparison

### Scenario: Route with 5 relevant cameras

**Old Method (Repository)**:
```
1. repository.list_cameras()           → 1 query (returns 90 IDs)
2. repository.get_camera_metadata()    → 90 queries
3. Filter geometrically                → In-memory
4. repository.get_forecast()           → 5 queries
Total: 96 queries
```

**New Method (JSON File)**:
```
1. loader.load_cameras()               → 0 queries (reads JSON file once)
2. Filter geometrically                → In-memory
3. repository.get_forecast()           → 5 queries
Total: 5 queries
```

**Improvement**: ~95% reduction in database queries

## Testing

### Unit Test

```python
def test_camera_loader():
    loader = get_camera_loader()
    cameras = loader.load_cameras()
    
    assert len(cameras) == 90
    assert cameras[0].camera_id == "1001"
    
    # Test filtering
    cam = loader.get_camera_by_id("1001")
    assert cam is not None
```

### Integration Test

```bash
python test_route_optimization.py

# All tests pass:
# ✓ Camera loader works
# ✓ Haversine distance calculation
# ✓ Camera finding along route
# ...
```

## Configuration

No configuration needed! The camera file location is automatic:

```python
DEFAULT_CAMERA_FILE = Path(__file__).parent.parent / "train" / "data" / "cam_id_lat_lon.json"
```

**Resolves to**: 
`backend/app/services/trafficcams/train/data/cam_id_lat_lon.json`

## Benefits

✅ **Performance**: Fewer database queries
✅ **Simplicity**: Clear data source
✅ **Maintainability**: Camera locations rarely change
✅ **Scalability**: In-memory cache, O(1) lookups
✅ **Testability**: Easy to test without database

## When to Update Camera Data

The JSON file should be updated when:
1. New cameras are deployed
2. Camera locations change
3. Cameras are decommissioned

**Update Process**:
1. Edit `train/data/cam_id_lat_lon.json`
2. Restart the service (cache will reload)
3. No code changes needed!

## Architecture Decision

**Why JSON file instead of database?**

1. **Camera metadata is static** - Changes rarely
2. **Read-heavy** - Never written at runtime
3. **Performance** - Loading 90 records from JSON is instant
4. **Separation of concerns** - Static data vs. dynamic CI/forecasts
5. **Simplicity** - No need to populate database with metadata

**What stays in database?**
- Current CI values (changes every 2 minutes)
- Forecasts (changes every 2 minutes)
- Historical data (for ML training)

This follows the principle: **Static data in files, dynamic data in database**.
