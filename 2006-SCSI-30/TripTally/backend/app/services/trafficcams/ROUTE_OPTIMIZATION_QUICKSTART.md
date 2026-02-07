# Route Optimization Quick Start Guide

## 🚀 Quick Start

### 1. Start the Service

```bash
# Ensure Redis is running (if using Redis repository)
docker-compose up -d redis

# Start FastAPI backend
cd TripTally/backend
uvicorn app.main:app --reload --port 8000
```

### 2. Test the API

**Find cameras along a route:**
```bash
curl "http://localhost:8000/api/traffic/route/cameras-along-route?points=1.3521,103.8198,1.3621,103.8298&radius_km=0.5"
```

**Optimize departure time:**
```bash
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

### 3. Check API Documentation

Visit: `http://localhost:8000/docs`

## 📊 API Endpoints

### POST `/api/traffic/route/optimize`

**Purpose**: Find optimal departure time for a route

**Request Body**:
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
  "cameras_found": 5,
  "route_length_km": 12.5,
  "best_departure": {
    "departure_time": "2025-11-03T14:30:00",
    "minutes_from_now": 30,
    "average_ci": 0.35,
    "traffic_level": "light",
    "estimated_travel_time_minutes": 25.3,
    "new_eta": "2025-11-03T14:55:18",
    "confidence_score": 0.82
  },
  "alternative_departures": [...]
}
```

### GET `/api/traffic/route/cameras-along-route`

**Purpose**: Get cameras near a route (lightweight)

**Parameters**:
- `points`: Comma-separated lat,lon pairs
- `radius_km`: Search radius (default: 0.5)

**Example**:
```
GET /api/traffic/route/cameras-along-route?points=1.35,103.82,1.36,103.83&radius_km=0.5
```

### GET `/api/traffic/route/health`

**Purpose**: Check service health

**Response**:
```json
{
  "status": "healthy",
  "repository": "Redis",
  "repository_healthy": true
}
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Router                     │
│         /api/traffic/route/optimize                  │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │ RouteOptimization  │
         │     Service        │
         └─────┬──────┬───────┘
               │      │
       ┌───────▼──┐   └───────▼──────────┐
       │ Geospatial│   │  DataRepository  │
       │  Service  │   │  (Redis/CSV/SQL) │
       └───────────┘   └──────────────────┘
```

## 🔧 Configuration

Uses existing environment variables:

```bash
# Repository backend
REPOSITORY_TYPE=redis  # or csv, sql

# Forecaster type
FORECASTER_TYPE=auto   # or simple, ml

# Redis (if using Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 📝 Usage Examples

### Python

```python
import requests

def optimize_my_route():
    response = requests.post(
        "http://localhost:8000/api/traffic/route/optimize",
        json={
            "route_points": [
                {"latitude": 1.3521, "longitude": 103.8198},
                {"latitude": 1.3621, "longitude": 103.8298}
            ],
            "estimated_travel_time_minutes": 30
        }
    )
    
    result = response.json()
    best = result['best_departure']
    
    print(f"Leave in: {best['minutes_from_now']} minutes")
    print(f"Traffic: {best['traffic_level']}")
    print(f"New ETA: {best['new_eta']}")
    
    return result
```

### JavaScript/TypeScript

```typescript
async function optimizeRoute(points: {lat: number, lon: number}[]) {
  const response = await fetch('/api/traffic/route/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      route_points: points.map(p => ({
        latitude: p.lat,
        longitude: p.lon
      })),
      estimated_travel_time_minutes: 30
    })
  });
  
  const result = await response.json();
  return result;
}
```

### cURL

```bash
# Simple test
curl -X POST http://localhost:8000/api/traffic/route/optimize \
  -H "Content-Type: application/json" \
  -d @route_request.json

# route_request.json:
{
  "route_points": [
    {"latitude": 1.3521, "longitude": 103.8198},
    {"latitude": 1.3621, "longitude": 103.8298}
  ],
  "estimated_travel_time_minutes": 30
}
```

## 🧪 Testing

```bash
# Run unit tests
cd backend/app/services/trafficcams
python test_route_optimization.py

# Expected output:
# ======================================================================
# ROUTE OPTIMIZATION SERVICE TESTS
# ======================================================================
# [TEST] Haversine Distance Calculation
#   ✓ Distance calculation correct
# [TEST] Point to Line Distance
#   ✓ Point-to-line calculation correct
# ...
# RESULTS: 6 passed, 0 failed
```

## 📊 Traffic Levels

| CI Range  | Level       | Speed Factor | Description           |
|-----------|-------------|-------------|-----------------------|
| 0.0-0.3   | Free Flow   | 100%        | No congestion         |
| 0.3-0.5   | Light       | 90%         | Minor slowdowns       |
| 0.5-0.7   | Moderate    | 70%         | Noticeable delays     |
| 0.7-0.9   | Heavy       | 50%         | Significant congestion|
| 0.9-1.0   | Severe      | 30%         | Gridlock              |

## 🎯 How It Works

1. **Find Cameras**: Identifies all traffic cameras within 500m of your route
2. **Get Traffic Data**: Retrieves current CI and forecasts for each camera
3. **Analyze Times**: Evaluates departure every 10 minutes for next 2 hours
4. **Estimate Travel Time**: Adjusts travel time based on congestion
5. **Pick Best Time**: Selects departure with lowest average traffic
6. **Calculate New ETA**: Provides updated arrival time

## 🔍 Confidence Score

The confidence score (0.0 to 1.0) indicates reliability:

- **> 0.8**: High confidence (many cameras, short horizon)
- **0.5-0.8**: Moderate confidence
- **< 0.5**: Low confidence (few cameras or long horizon)

Factors:
- Number of cameras along route (more = better)
- Forecast horizon (closer = better)
- Data availability (complete = better)

## 🚨 Error Handling

**Common Issues**:

```json
// Invalid route (< 2 points)
{
  "detail": "route_points must have at least 2 points"
}

// Service unavailable
{
  "detail": "Route optimization failed: repository not available"
}
```

## 💡 Tips

1. **Use adequate search radius**: 0.5 km works well for urban areas
2. **More route points = better**: Break long routes into segments
3. **Check confidence score**: Higher = more reliable
4. **Consider alternatives**: Sometimes 2nd or 3rd option is better
5. **Monitor traffic levels**: "moderate" or higher warrants departure time adjustment

## 📚 Further Reading

- **Full Documentation**: `ROUTE_OPTIMIZATION_README.md`
- **API Docs**: `http://localhost:8000/docs`
- **Design Patterns**: `DESIGN_PATTERNS.md`
- **Testing Guide**: `TESTING_RESULTS.md`

## 🤝 Integration with Frontend

### Example: React Component

```tsx
import { useState } from 'react';

function RouteOptimizer({ route }) {
  const [result, setResult] = useState(null);
  
  const optimize = async () => {
    const response = await fetch('/api/traffic/route/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        route_points: route.map(p => ({
          latitude: p.lat,
          longitude: p.lng
        })),
        estimated_travel_time_minutes: 30
      })
    });
    
    setResult(await response.json());
  };
  
  return (
    <div>
      <button onClick={optimize}>Optimize Departure</button>
      {result && (
        <div>
          <p>Best time: {result.best_departure.minutes_from_now} min</p>
          <p>Traffic: {result.best_departure.traffic_level}</p>
          <p>ETA: {result.best_departure.new_eta}</p>
        </div>
      )}
    </div>
  );
}
```

## 🎓 Key Concepts

- **LineString**: Your route represented as ordered points
- **CI (Congestion Index)**: 0.0 (free) to 1.0 (gridlock)
- **Horizon**: How far into the future (0-120 minutes)
- **Position on Route**: 0.0 (start) to 1.0 (end)
- **Search Radius**: How far from route to look for cameras

---

**Ready to optimize your routes! 🚗💨**
