# Simple CI with Redis Integration

This implementation continuously processes traffic camera images, calculates Congestion Index (CI), generates forecasts, and stores everything in Redis.

## Architecture

```
┌─────────────────┐
│  Traffic Camera │
│      API        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────┐
│  simple_ci_     │─────▶│    Redis    │
│    redis.py     │      │   Cache     │
│  (runs every    │◀─────│             │
│   2 minutes)    │      └──────┬──────┘
└─────────────────┘             │
         │                      │
         │                      ▼
         ▼              ┌──────────────┐
    Forecasting         │  FastAPI     │
    (persistence +      │  Endpoints   │
     mean reversion)    │              │
                        └──────────────┘
```

## Components

### 1. **simple_ci_redis.py**
Main processing script that:
- Fetches traffic camera images from Singapore LTA API
- Runs YOLO object detection to count vehicles
- Calculates motion score using frame differencing
- Computes Congestion Index (CI) from vehicle density, area coverage, and motion
- Generates forecasts for 2, 4, 6, ..., 120 minutes ahead
- Stores current state and forecasts in Redis
- Runs continuously with 2-minute intervals

### 2. **Redis Data Structure**

#### Current State: `ci:now:<camera_id>`
Hash containing:
```
{
  "ts": "2025-11-03T10:30:00+00:00",
  "camera_id": "1234",
  "img_w": "1280",
  "img_h": "720",
  "veh_count": "15",
  "veh_wcount": "18.5",
  "area_ratio": "0.045",
  "motion": "2.3",
  "CI": "0.67",
  "minute_of_day": "630",
  "hour": "10",
  "day_of_week": "0",
  "is_weekend": "False",
  "sin_t_h": "0.866",
  "cos_t_h": "0.5",
  "model_ver": "simple_ci_v1"
}
```
TTL: 600 seconds (10 minutes)

#### Forecast: `ci:fcst:<camera_id>`
Hash containing:
```
{
  "ts": "2025-11-03T10:30:00+00:00",
  "camera_id": "1234",
  "model_ver": "simple_ci_v1",
  "h:2": "0.68",
  "h:4": "0.69",
  "h:6": "0.70",
  ...
  "h:120": "0.55"
}
```
TTL: 600 seconds (10 minutes)

#### Camera Metadata: `cameras:meta`
Hash mapping camera_id to metadata JSON

### 3. **API Endpoints**

Defined in `simple_camera_routes.py`:

#### GET `/api/cameras/{cid}/now`
Get current CI state for a camera.

**Response:**
```json
{
  "ts": "2025-11-03T10:30:00+00:00",
  "camera_id": "1234",
  "CI": 0.67,
  "veh_count": 15,
  "area_ratio": 0.045,
  "motion": 2.3,
  "model_ver": "simple_ci_v1"
}
```

#### GET `/api/cameras/{cid}/forecast`
Get CI forecasts for a camera.

**Response:**
```json
{
  "ts": "2025-11-03T10:30:00+00:00",
  "camera_id": "1234",
  "horizons_min": [2, 4, 6, 8, ..., 120],
  "CI_forecast": [0.68, 0.69, 0.70, ..., 0.55],
  "model_ver": "simple_ci_v1"
}
```

#### GET `/api/cameras/health`
Health check endpoint.

## Setup

### Prerequisites
1. Redis server running
2. YOLO ONNX model file (`model.onnx`)
3. Python dependencies installed

### Environment Variables

```bash
# API Configuration
API_URL=https://api.data.gov.sg/v1/transport/traffic-images
X_API_KEY=your_api_key_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Model Configuration
MODEL_PATH=model.onnx
IMG_SIZE=640
CONF_THRES=0.25
IOU_THRES=0.45

# CI Parameters
K_COUNT=20
K_AREA=0.10
K_MOTION=8.0
W_DENS=0.6
W_AREA=0.4
W_MREL=0.3
W_CIRAW=0.7
CI_ALPHA=0.4

# Loop Configuration
LOOP_INTERVAL=120  # seconds (2 minutes)
CACHE_DIR=./cache

# Verbosity
VERBOSE=1
```

### Installation

1. **Install Dependencies:**
   ```bash
   cd TripTally/backend/app/services/trafficcams
   pip install -r requirements.txt
   ```

2. **Start Redis:**
   ```bash
   redis-server
   ```

3. **Run CI Processing:**
   ```bash
   python simple_ci_redis.py
   ```

4. **Add Routes to FastAPI App:**
   
   In `app/main.py`:
   ```python
   from app.api.simple_camera_routes import router as camera_router
   
   app.include_router(camera_router)
   ```

5. **Start FastAPI:**
   ```bash
   cd TripTally/backend
   uvicorn app.main:app --reload
   ```

## Forecasting Method

Simple **persistence with mean reversion** model:

1. **History Tracking:** Maintains last 60 observations per camera (~2 hours)
2. **Trend Calculation:** Linear trend from last 10 observations
3. **Mean Reversion:** Exponential decay to historical mean
4. **Formula:**
   ```
   CI(t+h) = CI(t) + trend × h + (1 - decay) × (mean - CI(t))
   
   where:
   - h = forecast horizon (minutes)
   - decay = exp(-h / 60)  # 60-minute half-life
   - mean = average of last 30 observations
   - trend = linear trend from last 10 observations
   ```

This approach:
- Uses current value as baseline (persistence)
- Incorporates recent trend
- Gradually reverts to mean for longer horizons
- More conservative and stable than pure persistence

## Testing

### Test Current State
```bash
curl http://localhost:8000/api/cameras/1001/now
```

### Test Forecast
```bash
curl http://localhost:8000/api/cameras/1001/forecast
```

### Test Health
```bash
curl http://localhost:8000/api/cameras/health
```

### Monitor Redis
```bash
redis-cli

# Check current state
HGETALL ci:now:1001

# Check forecast
HGETALL ci:fcst:1001

# Check all cameras
HGETALL cameras:meta

# Monitor in real-time
MONITOR
```

## Monitoring

The script logs:
- API fetch time
- Processing time per camera
- Detection results (boxes, CI values)
- Redis write operations
- Summary statistics per iteration

Example log output:
```
[10:30:15] Init: MODEL=model.onnx IMG_SIZE=640 CONF=0.25 IOU=0.45
[10:30:15] Redis: localhost:6379 DB=0
[10:30:15] Loop interval: 120s
[10:30:15] Redis connection OK
[10:30:15] === Iteration 1 ===
[10:30:16] API fetch OK in 234.5 ms
[10:30:16] Timestamp=2025-11-03T10:30:00+08:00 cameras=87
[10:30:17] cam=1001 1280x720 dl=145.2ms infer=89.3ms boxes=15 veh_w=18.5 area=0.045 motion=2.30 CI=0.670
...
[10:31:23] SUMMARY: ok_imgs=85/87 total_boxes=1247 mean_boxes/img=14.67 total_time=67234ms
[10:31:23] Sleeping 120s until next iteration...
```

## Troubleshooting

### Redis Connection Errors
```bash
# Check if Redis is running
redis-cli ping

# Check Redis logs
redis-server --loglevel verbose
```

### Missing ONNX Model
```bash
# Download or convert YOLO model to ONNX format
# Place in services/trafficcams/ directory
```

### API Rate Limiting
- Ensure X_API_KEY is set correctly
- Check LTA API quotas
- Increase LOOP_INTERVAL if needed

### Stale Data (503 errors)
- Check if simple_ci_redis.py is running
- Verify loop interval (should be ≤ 2 minutes)
- Check Redis TTL settings

## Performance

On typical hardware:
- **Image download:** ~150ms per camera
- **YOLO inference:** ~90ms per camera (CPU)
- **Total per iteration:** ~60-90 seconds for 87 cameras
- **Memory usage:** ~500MB (including YOLO model)
- **Redis storage:** ~50KB per camera (current + forecast)

## Future Improvements

1. **Better Forecasting:**
   - Train ML model (LSTM, XGBoost) on historical data
   - Include weather, events, day-of-week patterns
   - Multi-step forecasting with uncertainty estimates

2. **Optimization:**
   - GPU acceleration for YOLO
   - Parallel image downloads
   - Redis pipelining for batch writes

3. **Features:**
   - Incident detection (sudden CI spikes)
   - Route congestion aggregation
   - Historical data export for training
   - Real-time alerts via WebSocket

4. **Reliability:**
   - Retry logic for failed cameras
   - Graceful degradation if Redis unavailable
   - Backup to disk if Redis down
   - Health metrics export (Prometheus)
