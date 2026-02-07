# TripTally Command Cheat Sheet

Quick reference for common commands.

## One-Line Setup

```powershell
# Start Redis + Backend + Traffic CI + Frontend (run each in separate terminal)
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine ; cd TripTally/backend ; uvicorn app.main:app --reload
cd TripTally/backend/app/services/trafficcams ; python simple_ci_redis.py
cd TripTally/frontend ; npx expo start
```

## Redis Commands

```powershell
# Start Redis
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Start existing Redis
docker start triptally-redis

# Stop Redis
docker stop triptally-redis

# Remove Redis (deletes data)
docker rm -f triptally-redis

# View logs
docker logs -f triptally-redis

# Access Redis CLI
docker exec -it triptally-redis redis-cli

# Test connection
docker exec -it triptally-redis redis-cli ping
```

## Redis Data Commands

```powershell
# Inside Redis CLI (docker exec -it triptally-redis redis-cli)

# List all cameras
KEYS ci:now:*

# Get camera 1001 current state
HGETALL ci:now:1001

# Get specific field
HGET ci:now:1001 CI

# Get forecast
HGETALL ci:fcst:1001

# Count keys
DBSIZE

# Monitor real-time updates
MONITOR

# Clear all data (destructive)
FLUSHALL
```

## Backend Commands

```powershell
# Start backend
cd TripTally/backend
uvicorn app.main:app --reload

# Start with specific host/port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test
pytest tests/test_api_endpoint.py -v
```

## Traffic CI Service Commands

```powershell
# Start service
cd TripTally/backend/app/services/trafficcams
python simple_ci_redis.py

# Start with custom config
python simple_ci_redis.py --loop-interval 300 --verbose

# Run once (no loop)
python simple_ci.py

# Test with sample data
python -m pytest tests/
```

## Frontend Commands

```powershell
# Start Expo
cd TripTally/frontend
npx expo start

# Start with cache clear
npx expo start -c

# Web only
npm run web

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Testing Commands

```powershell
# Test backend health
curl http://localhost:8000/health

# Test camera current state
curl http://localhost:8000/api/cameras/1001/now

# Test camera forecast
curl http://localhost:8000/api/cameras/1001/forecast

# Test with formatted output (requires jq)
curl http://localhost:8000/api/cameras/1001/now | jq

# Test Redis connection
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
```

## Docker Compose Commands

```powershell
cd TripTally/infra

# Start dev environment
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild
docker compose up -d --build

# Remove volumes (deletes data)
docker compose down -v
```

## Troubleshooting Commands

```powershell
# Check what's running on port 8000
netstat -ano | findstr :8000

# Check what's running on port 6379
netstat -ano | findstr :6379

# Kill process by PID
taskkill /PID <pid> /F

# Check Docker containers
docker ps -a

# Check Docker logs
docker logs triptally-redis

# Restart Docker Desktop
# Right-click Docker Desktop tray icon -> Restart
```

## Common Workflows

### Daily Development Start
```powershell
# Terminal 1
docker start triptally-redis

# Terminal 2
cd TripTally/backend ; uvicorn app.main:app --reload

# Terminal 3
cd TripTally/backend/app/services/trafficcams ; python simple_ci_redis.py

# Terminal 4
cd TripTally/frontend ; npx expo start
```

### Daily Development Stop
```powershell
# Press Ctrl+C in each terminal

# Then stop Redis
docker stop triptally-redis
```

### Fresh Start (Clean Everything)
```powershell
# Stop and remove Redis
docker rm -f triptally-redis

# Start fresh Redis
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Clear Python cache
cd TripTally/backend
Remove-Item -Recurse -Force __pycache__,*.pyc

# Restart backend
uvicorn app.main:app --reload
```

### Debug Redis Connection
```powershell
# Check Redis is running
docker ps | Select-String redis

# Test connection from CLI
docker exec -it triptally-redis redis-cli ping

# Test from Python
cd TripTally/backend
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print('Connected!' if r.ping() else 'Failed')"

# Check backend .env
cd TripTally/backend
cat .env | Select-String REDIS
```

### View Traffic CI Data
```powershell
# Access Redis
docker exec -it triptally-redis redis-cli

# In Redis CLI:
KEYS ci:now:*                    # List all current states
HGETALL ci:now:1001              # Get camera 1001 data
HGET ci:now:1001 CI              # Get just CI value
HGET ci:now:1001 ts              # Get timestamp
HGETALL ci:fcst:1001             # Get forecast
```

## Monitoring Commands

```powershell
# Watch Docker stats
docker stats triptally-redis

# Monitor Redis commands
docker exec -it triptally-redis redis-cli MONITOR

# Watch backend logs
cd TripTally/backend
Get-Content app.log -Wait

# Watch CI service output
# Just let it run in terminal - it outputs continuously
```

## Maintenance Commands

```powershell
# Update Python dependencies
cd TripTally/backend
pip install -r requirements.txt --upgrade

# Update Node dependencies
cd TripTally/frontend
npm update

# Check for outdated packages
npm outdated

# Clear Expo cache
npx expo start -c

# Clear Python cache
cd TripTally/backend
py -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
py -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
```

## Environment Setup

```powershell
# Copy environment template
cd TripTally/backend
cp .env.example .env

# Edit environment
notepad .env

# Check environment variables
cat .env

# Verify API keys are set
cat .env | Select-String "KEY"
```

## 📸 Camera IDs Reference

Common camera IDs to test:
- `1001` - Typical camera ID
- `1002` - Another camera
- `1501` - Highway camera
- `2701` - City camera

```powershell
# Test multiple cameras
curl http://localhost:8000/api/cameras/1001/now
curl http://localhost:8000/api/cameras/1002/now
curl http://localhost:8000/api/cameras/1501/now
```

---

**Tip:** Bookmark this file for quick command lookup!
