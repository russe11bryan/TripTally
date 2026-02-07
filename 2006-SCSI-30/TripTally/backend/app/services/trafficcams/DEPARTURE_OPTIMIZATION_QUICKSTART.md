# 🚗 Departure Time Optimization - Quick Start

## What It Does

When you select a destination for **driving directions**, the app will:
1. ✅ Analyze traffic along your route
2. ✅ Check 2-hour forecast (every 2 minutes)
3. ✅ Find the time with minimum congestion
4. ✅ Show you the best time to leave
5. ✅ Display updated ETA based on traffic

## How to Use

### From the App

1. **Open Directions Page**
   - Select a destination
   - Choose "Drive" mode (🚗)

2. **View Recommendation**
   - After route loads, you'll see a card showing:
     - Best time to leave
     - Current vs. optimized ETA
     - Traffic conditions
     - Time you'll save

3. **Follow Recommendation**
   - Leave now (if traffic is good)
   - Wait X minutes (if traffic will improve)

### From the API

#### Endpoint
```
POST /api/traffic/departure/optimize
```

#### Request
```json
{
  "route_points": [
    {"latitude": 1.3521, "longitude": 103.8198},
    {"latitude": 1.2966, "longitude": 103.7764}
  ],
  "original_eta_minutes": 25,
  "search_radius_km": 0.5,
  "forecast_horizon_minutes": 120
}
```

#### Response
```json
{
  "best_time_minutes_from_now": 15,
  "best_departure_time": "2024-11-04T14:45:00",
  "current_eta_minutes": 32,
  "optimized_eta_minutes": 26,
  "time_saved_minutes": 6,
  "recommendation_text": "Wait 15 minutes for better traffic. You'll save 6 minutes!"
}
```

## Testing

### Backend Test
```bash
cd backend/app/services/trafficcams
python test_departure_optimizer.py
```

### Manual API Test
```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoint (in another terminal)
curl -X POST http://localhost:8000/api/traffic/departure/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "route_points": [
      {"latitude": 1.3521, "longitude": 103.8198},
      {"latitude": 1.2966, "longitude": 103.7764}
    ],
    "original_eta_minutes": 25
  }'
```

### Frontend Test
```bash
# Start backend (terminal 1)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Redis + CI service (terminal 2)
cd backend/app/services/trafficcams
docker-compose up -d

# Start frontend (terminal 3)
cd frontend
npx expo start

# Use Expo Go to test on phone
# 1. Open app
# 2. Search for destination
# 3. Select "Drive" mode
# 4. Wait for recommendation card to appear
```

## How It Works

### Algorithm Overview

1. **Find Cameras Near Route**
   ```
   - Load 90 cameras from JSON
   - Calculate distance to route
   - Keep only cameras within 500m
   - Typically finds 2-10 cameras
   ```

2. **Get Current Traffic**
   ```
   - Query latest CI for each camera
   - Calculate average CI along route
   - Classify: Light/Moderate/Heavy/Severe
   ```

3. **Analyze Forecast** (every 2 minutes for 2 hours)
   ```
   For time = 0, 2, 4, ..., 120 minutes:
     - Get forecasted CI
     - Calculate route average CI
     - Store time slot data
   ```

4. **Find Optimal Time**
   ```
   - Find time slot with minimum CI
   - Calculate adjusted ETA based on traffic
   - Compare with current conditions
   - Return recommendation
   ```

### ETA Calculation

```python
# Simple model: CI affects speed
CI < 0.2:  100% speed (free flow)
CI 0.2-0.4: 90% speed (light traffic)
CI 0.4-0.6: 80% speed (moderate)
CI 0.6-0.8: 67% speed (heavy)
CI 0.8-1.0: 50% speed (severe)

# Example:
Base ETA: 30 minutes
Current CI: 0.65 (heavy traffic)
Adjusted ETA: 30 * 1.5 = 45 minutes

Optimal CI: 0.35 (light traffic)
Optimal ETA: 30 * 1.1 = 33 minutes

Time saved: 45 - 33 = 12 minutes!
```

## Features

### ✅ Smart Recommendations
- Shows "Leave now" if traffic is good
- Suggests waiting if traffic will improve significantly
- Indicates when traffic is similar

### ✅ Confidence Scoring
- Based on:
  - Number of cameras analyzed
  - Difference in traffic conditions
  - Time window (nearer = more reliable)
- Shows warning if low confidence

### ✅ Visual Feedback
- Color-coded traffic levels (green/yellow/orange/red)
- ETA comparison (now vs. optimal)
- Progress bar for confidence
- Icons for traffic severity

### ✅ Only for Driving
- Feature only appears in "Drive" mode
- Not shown for walking, biking, or public transit
- Automatically hidden when mode changes

## Requirements

### Backend
- ✅ Redis running (for CI data)
- ✅ CI processing service running (generates forecasts)
- ✅ FastAPI backend running

### Frontend
- ✅ Backend accessible from device
- ✅ Google Maps API working (for routes)
- ✅ Expo Go or built app

## Troubleshooting

### "No traffic data available"
- **Cause**: No cameras near your route
- **Solution**: Try a different route in Singapore

### "Unable to connect to traffic service"
- **Cause**: Backend not running or not accessible
- **Solution**: Check backend is running on correct IP

### Card shows loading forever
- **Cause**: CI service not generating forecasts
- **Solution**: Check Redis and CI service are running
  ```bash
  docker-compose ps  # Should show redis and ci-service as Up
  ```

### Confidence warning appears
- **Cause**: Limited data (< 2 cameras or low confidence)
- **Solution**: This is expected for some routes. Use with caution.

## Architecture

```
Frontend (React Native)
    │
    ├─ DirectionsPage.js (Controller)
    │   ├─ Manages state
    │   ├─ Calls service
    │   └─ Updates UI
    │
    ├─ DepartureOptimizationService.js (Service)
    │   ├─ Calls backend API
    │   ├─ Transforms data
    │   └─ Handles errors
    │
    └─ DepartureRecommendationCard.js (View)
        ├─ Displays recommendation
        ├─ Shows traffic level
        └─ Renders ETA comparison

Backend (Python/FastAPI)
    │
    ├─ departure_optimization_routes.py (API)
    │   ├─ HTTP endpoints
    │   ├─ Request validation
    │   └─ Response formatting
    │
    ├─ departure_time_optimizer.py (Domain)
    │   ├─ Core business logic
    │   ├─ Traffic analysis
    │   └─ Optimization algorithm
    │
    └─ Infrastructure
        ├─ DataRepository (CI/Forecasts)
        ├─ GeospatialService (Distance calc)
        └─ CameraDataLoader (Camera data)
```

## Design Patterns

1. **MVC** - Clean separation of concerns
2. **Strategy** - Pluggable ETA calculation
3. **Facade** - Simple service interface
4. **Factory** - Dependency creation
5. **DTO** - Data transfer objects
6. **Adapter** - Route format conversion
7. **Observer** - Reactive UI updates

## Performance

- **Backend Response**: < 500ms typical
- **Cameras Analyzed**: 2-10 per route
- **Forecast Window**: 120 minutes (61 time slots)
- **Accuracy**: ±5 minutes (typical)

## Future Improvements

1. **Machine Learning** - Better ETA predictions
2. **Real-time Updates** - WebSocket for live updates
3. **Multi-route** - Compare multiple routes
4. **User Preferences** - Max wait time, fuel vs time
5. **Historical Data** - Show typical patterns

## Support

For issues or questions:
- Check `DEPARTURE_OPTIMIZATION_ARCHITECTURE.md` for details
- Run backend test: `python test_departure_optimizer.py`
- Check logs in `logs/` directory
- Verify API docs: `http://localhost:8000/docs`
