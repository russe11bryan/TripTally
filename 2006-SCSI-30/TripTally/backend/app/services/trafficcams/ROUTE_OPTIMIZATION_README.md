# Route Optimization Service

## Overview

The Route Optimization Service analyzes traffic conditions along a planned route and recommends the best time to depart based on real-time and forecasted congestion data.

## Architecture

### Design Principles

**✅ Loose Coupling**: Components interact through well-defined interfaces
- `DataRepository` interface allows swapping storage backends (Redis/CSV/SQL)
- `GeospatialService` is independent and reusable
- `RouteOptimizationService` depends only on abstractions

**✅ Single Responsibility**: Each component has one clear purpose
- `GeospatialService`: Geographic calculations only
- `RouteOptimizationService`: Business logic for optimization
- API layer: HTTP request/response handling only

**✅ Dependency Injection**: Dependencies passed via constructor
```python
optimizer = RouteOptimizationService(
    repository=repository,
    geospatial_service=geo_service
)
```

**✅ Domain-Driven Design**: Clear separation of concerns
```
domain/          # Business logic (no frameworks)
├── route_models.py       # Domain entities
├── geospatial_service.py # Geographic calculations  
└── route_optimizer.py    # Core optimization logic

api/             # Application layer
└── route_optimization_routes.py  # FastAPI endpoints
```

## Components

### 1. Domain Models (`domain/route_models.py`)

**Purpose**: Define business entities

**Models**:
- `Point`: Geographic coordinate (lat, lon)
- `LineString`: Route as series of points
- `RouteCameraInfo`: Camera metadata with route position
- `CameraTrafficInfo`: Traffic data for a camera at a time
- `DepartureOption`: Departure time analysis result
- `RouteOptimizationResult`: Complete optimization output
- `TrafficLevel`: Enum for CI classification

**Dependencies**: None (pure domain models)

### 2. Geospatial Service (`domain/geospatial_service.py`)

**Purpose**: Geographic calculations and camera-route matching

**Key Methods**:
- `haversine_distance()`: Distance between two points
- `point_to_line_distance()`: Distance from point to line segment
- `find_cameras_along_route()`: Find cameras within radius of route
- `calculate_route_length()`: Total route distance

**Algorithm**: 
- Projects each camera onto nearest route segment
- Calculates perpendicular distance
- Returns cameras within search radius sorted by position

**Dependencies**: None (pure math)

### 3. Route Optimization Service (`domain/route_optimizer.py`)

**Purpose**: Core business logic for finding optimal departure time

**Constructor**:
```python
def __init__(
    self,
    repository: DataRepository,
    geospatial_service: GeospatialService
)
```

**Key Method**:
```python
def optimize_route(
    route: LineString,
    original_eta_minutes: int,
    search_radius_km: float = 0.5,
    forecast_horizon_minutes: int = 120
) -> RouteOptimizationResult
```

**Algorithm**:
1. Query all cameras from repository
2. Find cameras along route using geospatial service
3. For each departure time (0, 10, 20...120 minutes):
   - Get current CI or forecast for each camera
   - Calculate average and max CI along route
   - Estimate travel time based on congestion
   - Calculate confidence score
4. Select best departure (lowest avg CI)
5. Return top options

**Travel Time Estimation**:
```python
CI Range  | Speed Factor | Effective Speed (60 km/h base)
----------|--------------|-------------------------------
0.0-0.3   | 100%        | 60 km/h (free flow)
0.3-0.5   | 90%         | 54 km/h (light traffic)
0.5-0.7   | 70%         | 42 km/h (moderate)
0.7-0.9   | 50%         | 30 km/h (heavy)
0.9-1.0   | 30%         | 18 km/h (severe)
```

**Dependencies**: 
- `DataRepository` (for camera data)
- `GeospatialService` (for route calculations)

### 4. API Layer (`api/route_optimization_routes.py`)

**Purpose**: HTTP interface for route optimization

**Endpoints**:

#### POST `/api/traffic/route/optimize`
Find optimal departure time for a route

**Request**:
```json
{
  "route_points": [
    {"latitude": 1.3521, "longitude": 103.8198},
    {"latitude": 1.3621, "longitude": 103.8298}
  ],
  "estimated_travel_time_minutes": 30,
  "search_radius_km": 0.5,
  "forecast_horizon_minutes": 120
}
```

**Response**:
```json
{
  "success": true,
  "message": "Found 5 cameras along route",
  "route_length_km": 12.5,
  "cameras_found": 5,
  "best_departure": {
    "departure_time": "2025-11-03T14:30:00",
    "minutes_from_now": 30,
    "average_ci": 0.35,
    "max_ci": 0.52,
    "estimated_travel_time_minutes": 25.3,
    "new_eta": "2025-11-03T14:55:18",
    "confidence_score": 0.82,
    "traffic_level": "light",
    "camera_count": 5
  },
  "alternative_departures": [...],
  "route_cameras": [...]
}
```

#### GET `/api/traffic/route/cameras-along-route`
Get cameras along route (lightweight)

**Query Parameters**:
- `points`: Comma-separated lat,lon pairs (e.g., "1.3521,103.8198,1.3621,103.8298")
- `radius_km`: Search radius (default: 0.5)

**Response**:
```json
{
  "success": true,
  "cameras_found": 5,
  "cameras": [
    {
      "camera_id": "1001",
      "latitude": 1.3541,
      "longitude": 103.8205,
      "distance_to_route_meters": 125.5,
      "position_on_route": 0.234
    }
  ]
}
```

#### GET `/api/traffic/route/health`
Health check

## Code Reuse

### From Existing Codebase

**✅ Data Repository Pattern**:
- Reuses `DataRepository` interface
- Works with Redis/CSV/SQL implementations
- No coupling to specific storage

**✅ Factory Pattern**:
- Uses `ServiceContext` to get repository
- Configuration-driven (environment variables)

**✅ Domain Models**:
- Reuses `Camera`, `CIState`, `CIForecast`
- Extends with new route-specific models

**✅ Logger**:
- Reuses existing logging infrastructure
- Consistent log format

**✅ Configuration**:
- Reuses `Config` system
- Same environment variables

### New Components (No Duplication)

- `GeospatialService`: New geographic calculations
- `RouteOptimizationService`: New business logic
- Route-specific domain models: New entities

## Testing

### Unit Tests

```python
# Test geospatial calculations
def test_haversine_distance():
    service = GeospatialService()
    dist = service.haversine_distance(1.3521, 103.8198, 1.3621, 103.8298)
    assert 10 < dist < 15  # Rough validation

# Test camera finding
def test_find_cameras_along_route():
    service = GeospatialService()
    route = LineString([Point(1.35, 103.82), Point(1.36, 103.83)])
    cameras = [Camera("1001", 1.355, 103.825, None)]
    result = service.find_cameras_along_route(route, cameras, 1.0)
    assert len(result) == 1

# Test optimization (with mock repository)
def test_optimize_route():
    mock_repo = MockRepository()
    geo_service = GeospatialService()
    optimizer = RouteOptimizationService(mock_repo, geo_service)
    
    route = LineString([Point(1.35, 103.82), Point(1.36, 103.83)])
    result = optimizer.optimize_route(route, 30)
    
    assert result.best_departure is not None
    assert 0 <= result.best_departure.average_ci <= 1.0
```

### Integration Tests

```bash
# Start service with test data
cd backend/app/services/trafficcams
python -m pytest test_route_optimization.py
```

### Manual API Testing

```bash
# Test cameras endpoint
curl "http://localhost:8000/api/traffic/route/cameras-along-route?points=1.3521,103.8198,1.3621,103.8298&radius_km=0.5"

# Test optimization endpoint
curl -X POST http://localhost:8000/api/traffic/route/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "route_points": [
      {"latitude": 1.3521, "longitude": 103.8198},
      {"latitude": 1.3621, "longitude": 103.8298}
    ],
    "estimated_travel_time_minutes": 30
  }'
```

## Usage Examples

### Python Client

```python
import requests

# Optimize route
response = requests.post(
    "http://localhost:8000/api/traffic/route/optimize",
    json={
        "route_points": [
            {"latitude": 1.3521, "longitude": 103.8198},
            {"latitude": 1.3621, "longitude": 103.8298},
            {"latitude": 1.3721, "longitude": 103.8398}
        ],
        "estimated_travel_time_minutes": 45,
        "search_radius_km": 0.5,
        "forecast_horizon_minutes": 120
    }
)

result = response.json()
print(f"Best departure: {result['best_departure']['minutes_from_now']} min from now")
print(f"Traffic level: {result['best_departure']['traffic_level']}")
print(f"New ETA: {result['best_departure']['new_eta']}")
```

### Frontend Integration

```typescript
interface RoutePoint {
  latitude: number;
  longitude: number;
}

async function optimizeRoute(
  points: RoutePoint[],
  etaMinutes: number
): Promise<any> {
  const response = await fetch('/api/traffic/route/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      route_points: points,
      estimated_travel_time_minutes: etaMinutes,
      search_radius_km: 0.5,
      forecast_horizon_minutes: 120
    })
  });
  
  return response.json();
}
```

## Performance Considerations

### Optimization

- **Camera Query**: O(n) where n = total cameras
- **Route Matching**: O(n × m) where m = route segments
- **Forecast Analysis**: O(k × c) where k = time horizons, c = route cameras

### Typical Performance

- 100 cameras, 10 route segments, 13 time horizons, 5 cameras on route
- Processing time: ~50-200ms (depends on repository)

### Caching Recommendations

1. Cache camera metadata (changes rarely)
2. Cache forecasts with TTL (updates every 2 minutes)
3. Consider caching route-camera matches for popular routes

## Configuration

Uses existing config system via environment variables:

```bash
# Repository selection
REPOSITORY_TYPE=redis  # or csv, sql

# Forecaster selection  
FORECASTER_TYPE=auto   # or simple, ml

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
```

No additional configuration needed!

## Extending the Service

### Add New Traffic Level Classification

```python
# In domain/route_models.py
class TrafficLevel(Enum):
    CUSTOM_LEVEL = "custom"
    
    @classmethod
    def from_ci(cls, ci: float) -> 'TrafficLevel':
        # Add custom logic
        pass
```

### Customize Travel Time Model

```python
# In domain/route_optimizer.py
class RouteOptimizationService:
    # Modify CI_SPEED_FACTORS
    CI_SPEED_FACTORS = {
        0.0: 1.0,
        0.2: 0.95,  # More granular
        # ...
    }
```

### Add New Endpoints

```python
# In api/route_optimization_routes.py
@router.post("/analyze-time-window")
async def analyze_time_window(...):
    # Custom analysis logic
    pass
```

## Benefits of This Architecture

✅ **Testable**: Each component can be tested independently
✅ **Maintainable**: Clear separation of concerns
✅ **Extensible**: Easy to add features without breaking existing code
✅ **Reusable**: Components can be used in other contexts
✅ **Scalable**: Stateless service, can be horizontally scaled
✅ **Flexible**: Works with any repository implementation (Redis/CSV/SQL)

## Future Enhancements

1. **Historical Analysis**: Compare predicted vs actual travel times
2. **Weather Integration**: Adjust forecasts based on weather
3. **Route Alternatives**: Suggest alternative routes
4. **Real-time Updates**: WebSocket for live traffic updates
5. **ML Optimization**: Use ML to improve departure recommendations
6. **Multi-modal**: Consider public transport schedules
