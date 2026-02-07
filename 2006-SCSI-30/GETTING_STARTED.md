# Quick Start: Running TripTally with Redis

This is the fastest way to get TripTally running with traffic camera congestion analysis.

## Prerequisites
- Docker Desktop installed
- Python 3.11+ installed
- Node.js 20+ installed

## Step-by-Step Guide (5 minutes)

### 1. Start Redis in Docker
```powershell
# Start Redis (runs in background)
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Verify it's running
docker ps

# Test connection
docker exec -it triptally-redis redis-cli ping
# Should return: PONG
```

### 2. Configure Backend
```powershell
cd TripTally/backend

# Copy environment template
cp .env.example .env

# Edit with your API keys
notepad .env
```

**Add these required keys to `.env`:**
```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys (get from respective websites)
TOMTOM_KEY=your_tomtom_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
LTA_ACCOUNT_KEY=your_lta_datamall_key

# Auth
SECRET_KEY=generate_a_random_32_character_secret_key_here

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 3. Start Backend
```powershell
# Install dependencies (first time only)
cd TripTally/backend
pip install -r requirements.txt

# Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend running at: **http://localhost:8000/docs**

### 4. Start Traffic Camera CI Service
```powershell
# Open a NEW terminal window
cd TripTally/backend/app/services/trafficcams

# Install dependencies (first time only)
pip install -r requirements.txt

# Verify Redis configuration in .env
# Should have:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REPOSITORY_TYPE=redis

# Start the CI service
python simple_ci_redis.py
```

You should see output like:
```
[10:30:15] Redis connection OK
[10:30:15] === Iteration 1 ===
[10:30:16] API fetch OK in 234.5 ms
[10:30:16] Timestamp=2025-11-08T10:30:00+08:00 cameras=87
[10:30:17] cam=1001 ... boxes=15 CI=0.670
[10:30:17] cam=1002 ... boxes=8 CI=0.420
...
```

### 5. Start Frontend
```powershell
# Open a NEW terminal window
cd TripTally/frontend

# Install dependencies (first time only)
npm install

# Start Expo
npx expo start
```

Frontend running at: **http://localhost:19006**

### 6. Test Everything

**Test Redis has data:**
```powershell
# Access Redis CLI
docker exec -it triptally-redis redis-cli

# Check for camera data
KEYS ci:now:*

# View specific camera data
HGETALL ci:now:1001

# Exit Redis CLI
exit
```

**Test Backend API:**
```powershell
# Health check
curl http://localhost:8000/health

# Get current congestion for camera 1001
curl http://localhost:8000/api/cameras/1001/now

# Get traffic forecast
curl http://localhost:8000/api/cameras/1001/forecast
```

## Daily Workflow

### Starting Everything
```powershell
# Terminal 1: Start Redis (if not running)
docker start triptally-redis

# Terminal 2: Backend
cd TripTally/backend
uvicorn app.main:app --reload

# Terminal 3: Traffic CI Service
cd TripTally/backend/app/services/trafficcams
python simple_ci_redis.py

# Terminal 4: Frontend
cd TripTally/frontend
npx expo start
```

### Stopping Everything
```powershell
# Stop each service with Ctrl+C in their terminals

# Stop Redis
docker stop triptally-redis

# Or stop and remove Redis
docker rm -f triptally-redis
```

## Useful Commands

### Redis Management
```powershell
# Start Redis
docker start triptally-redis

# Stop Redis
docker stop triptally-redis

# View Redis logs
docker logs -f triptally-redis

# Access Redis CLI
docker exec -it triptally-redis redis-cli

# Remove Redis (deletes all data)
docker rm -f triptally-redis
```

### Check What's Running
```powershell
# Check Redis
docker ps | Select-String triptally-redis

# Check backend (should show port 8000)
netstat -ano | findstr :8000

# Check Redis port
netstat -ano | findstr :6379
```

### View Traffic Camera Data in Redis
```powershell
docker exec -it triptally-redis redis-cli

# List all cameras with current data
KEYS ci:now:*

# Get all fields for camera 1001
HGETALL ci:now:1001

# Get specific field
HGET ci:now:1001 CI

# Get forecast data
HGETALL ci:fcst:1001

# Check how many keys
DBSIZE

# Monitor real-time updates
MONITOR
```

## Troubleshooting

### Redis won't start
```powershell
# Check if port 6379 is in use
netstat -ano | findstr :6379

# Use different port
docker run -d --name triptally-redis -p 6380:6379 redis:7-alpine

# Update .env with new port
# REDIS_PORT=6380
```

### CI Service says "Redis connection FAILED"
```powershell
# Check Redis is running
docker ps | Select-String triptally-redis

# Test connection
docker exec -it triptally-redis redis-cli ping

# Check .env has correct settings
cd TripTally/backend/app/services/trafficcams
cat .env | Select-String REDIS
```

### No data in Redis
```powershell
# Wait 2-3 minutes for first iteration
# Check CI service logs for errors
# Verify LTA_ACCOUNT_KEY is set in backend/.env
```

### Backend can't find Redis
```powershell
# Make sure REDIS_HOST=localhost in backend/.env
# Check Redis is on port 6379
docker ps

# Test from Python
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
```

## API Endpoints

Once everything is running:

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /health` | Backend health | http://localhost:8000/health |
| `GET /docs` | API documentation | http://localhost:8000/docs |
| `GET /api/cameras/{id}/now` | Current CI | http://localhost:8000/api/cameras/1001/now |
| `GET /api/cameras/{id}/forecast` | CI forecast | http://localhost:8000/api/cameras/1001/forecast |

## Services Overview

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Redis** | 6379 | - | Data cache for CI values |
| **Backend** | 8000 | http://localhost:8000 | FastAPI REST API |
| **CI Service** | - | - | Background processor |
| **Frontend** | 19006 | http://localhost:19006 | Expo web app |

## Next Steps

1. All services running
2. Open frontend: http://localhost:19006
3. Test API: http://localhost:8000/docs
4. View Redis data: `docker exec -it triptally-redis redis-cli`
5. Read full docs: `TripTally/infra/DOCKER_DEPLOYMENT.md`

## Getting API Keys

You need these API keys before starting:

1. **TomTom API Key**
   - Visit: https://developer.tomtom.com/
   - Sign up and create an API key
   - Free tier available

2. **Google Maps API Key**
   - Visit: https://developers.google.com/maps
   - Create a project and enable Maps JavaScript API
   - Generate credentials

3. **LTA DataMall Key**
   - Visit: https://datamall.lta.gov.sg/
   - Register for an account
   - Request API access
   - Get Account Key

4. **Google OAuth** (Optional - for sign-in)
   - Visit: https://console.cloud.google.com/
   - Create OAuth 2.0 credentials
   - Get Client ID and Secret

---

**That's it!** You now have TripTally running with real-time traffic congestion analysis powered by Redis.


Change Key.js to IP address