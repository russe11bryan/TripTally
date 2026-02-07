# TripTally

A comprehensive trip planning and comparison application that helps users find the best transportation routes with real-time traffic data and congestion analysis.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Quick Start Guide](#quick-start-guide)
- [Running with Docker](#running-with-docker)
- [Manual Setup](#manual-setup)
- [Traffic Camera CI Service](#traffic-camera-ci-service)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)

## Features

- **Multi-Modal Route Planning**: Compare driving, public transport, and campus shuttle routes
- **Real-Time Traffic Data**: Live traffic camera feeds and congestion information
- **Traffic Congestion Index (CI)**: ML-powered traffic prediction system
- **Cost Comparison**: Detailed fare calculations including ERP, parking, and transit costs
- **User Profiles**: Save favorite routes and preferences
- **Technical Reports**: Submit and track traffic incidents
- **Social Features**: Like and share route suggestions
- **OAuth Integration**: Google Sign-In support

## Getting Started

### Prerequisites

- **Docker Desktop** (Recommended) - [Download](https://www.docker.com/products/docker-desktop/)
- **Node.js** 20+ (for frontend development)
- **Python** 3.11+ (for backend development)
- **Git**

### Required API Keys

Before starting, obtain these API keys:
- **TomTom API Key**: [Get it here](https://developer.tomtom.com/)
- **Google Maps API Key**: [Get it here](https://developers.google.com/maps)
- **LTA DataMall Key**: [Get it here](https://datamall.lta.gov.sg/content/datamall/en.html)
- **Google OAuth Credentials** (optional): For authentication

## Quick Start Guide

### Option 1: Docker Setup (Recommended)

This is the easiest way to get everything running with Redis, PostgreSQL, and all services.

#### 1. Start Redis for Traffic Camera Service
```powershell
# Start Redis in Docker
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Verify Redis is running
docker ps | Select-String triptally-redis
```

#### 2. Configure Backend
```powershell
cd TripTally/backend

# Copy environment template
cp .env.example .env

# Edit .env with your API keys (use notepad or your preferred editor)
notepad .env
```

**Required environment variables in `.env`:**
```env
# Database (if using PostgreSQL)
DATABASE_URL=postgresql://triptally:password@localhost:5432/triptally

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys
TOMTOM_KEY=your_tomtom_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_key_here
LTA_ACCOUNT_KEY=your_lta_datamall_key_here

# Auth
SECRET_KEY=your_super_secret_key_min_32_characters_long

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

#### 3. Start Backend
```powershell
# Install dependencies
cd TripTally/backend
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000/docs**

#### 4. Start Traffic Camera CI Service
```powershell
# In a new terminal
cd TripTally/backend/app/services/trafficcams

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Configure for Redis
# The .env file should already have:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REPOSITORY_TYPE=redis

# Run the service
python simple_ci_redis.py
```

You should see:
```
[10:30:15] Redis connection OK
[10:30:15] === Iteration 1 ===
[10:30:16] API fetch OK in 234.5 ms
[10:30:17] Processing 87 cameras...
```

#### 5. Start Frontend
```powershell
# In a new terminal
cd TripTally/frontend

# Install dependencies
npm install

# Start Expo
npx expo start
```

Frontend will be available at: **http://localhost:19006**

#### 6. Verify Everything is Working

**Check Redis:**
```powershell
docker exec -it triptally-redis redis-cli
> KEYS ci:now:*
> HGETALL ci:now:1001
> exit
```

**Check Backend API:**
```powershell
# Health check
curl http://localhost:8000/health

# Traffic camera current state
curl http://localhost:8000/api/cameras/1001/now

# Traffic camera forecast
curl http://localhost:8000/api/cameras/1001/forecast
```

### Option 2: Full Docker Compose Setup

For a complete production-like setup with PostgreSQL, Redis, and all services:

```powershell
cd TripTally/infra

# Configure environment
cp .env.example .env
notepad .env  # Add your API keys

# Load PowerShell commands
. .\docker-commands.ps1

# Start development environment (includes Redis + PostgreSQL)
Start-Dev

# View logs
Show-Logs

# Access services:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - pgAdmin: http://localhost:5050 (if started with Start-DevTools)
```

See `TripTally/infra/README.md` for detailed Docker deployment guide.

## 🐳 Running with Docker

### Redis Only (Minimal Setup)

```powershell
# Start Redis
docker run -d --name triptally-redis `
  -p 6379:6379 `
  redis:7-alpine

# Stop Redis
docker stop triptally-redis

# Remove Redis
docker rm triptally-redis

# View Redis logs
docker logs -f triptally-redis
```

### Full Stack with Docker Compose

See `TripTally/infra/` directory for:
- **docker-compose.yml** - Production setup
- **docker-compose.dev.yml** - Development with hot reload
- **README.md** - Quick start guide
- **DOCKER_DEPLOYMENT.md** - Complete deployment guide

## 🔧 Manual Setup

### Backend Setup (Without Docker)

```powershell
cd TripTally/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
notepad .env  # Add your API keys

# Run migrations (if using PostgreSQL)
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```powershell
cd TripTally/frontend

# Install dependencies
npm install

# Start Expo
npx expo start

# Or for web only
npm run web
```

## 📸 Traffic Camera CI Service

The Traffic Camera Congestion Index (CI) service analyzes live traffic camera feeds to calculate real-time congestion and predict future traffic conditions.

### Features
- ✅ Real-time CI calculation for 87+ traffic cameras
- ✅ Vehicle detection using YOLO
- ✅ Motion analysis for flow estimation
- ✅ Forecasting (2-120 minutes ahead)
- ✅ Redis caching for fast API responses
- ✅ Runs continuously every 2 minutes

### Quick Start

1. **Start Redis:**
   ```powershell
   docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine
   ```

2. **Configure Service:**
   ```powershell
   cd TripTally/backend/app/services/trafficcams
   
   # Ensure .env has:
   # REDIS_HOST=localhost
   # REDIS_PORT=6379
   # REPOSITORY_TYPE=redis
   ```

3. **Run Service:**
   ```powershell
   python simple_ci_redis.py
   ```

4. **Test API:**
   ```powershell
   # Current congestion
   curl http://localhost:8000/api/cameras/1001/now
   
   # Forecast
   curl http://localhost:8000/api/cameras/1001/forecast
   ```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/cameras/{id}/now` | Current congestion state |
| `GET /api/cameras/{id}/forecast` | CI predictions (2-120 min) |
| `GET /api/cameras/health` | Service health check |

### Monitoring

**View Redis Data:**
```powershell
docker exec -it triptally-redis redis-cli

# List all cameras
KEYS ci:now:*

# Get current state for camera 1001
HGETALL ci:now:1001

# Get forecast
HGETALL ci:fcst:1001
```

**Service Logs:**
The CI service outputs real-time logs showing:
- API fetch times
- Processing times per camera
- Detection results (vehicle count, motion, CI)
- Errors and warnings

### Architecture

```
LTA Traffic API → CI Service → Redis → FastAPI Backend → Frontend
                      ↓
                 YOLO Detection
                 Motion Analysis
                 CI Calculation
                 Forecasting
```

See `TripTally/backend/app/services/trafficcams/docs/` for detailed documentation.

## 💻 Development Workflow

### Daily Development

```powershell
# 1. Start Redis
docker start triptally-redis

# 2. Start Backend
cd TripTally/backend
uvicorn app.main:app --reload

# 3. Start Traffic CI Service (in new terminal)
cd TripTally/backend/app/services/trafficcams
python simple_ci_redis.py

# 4. Start Frontend (in new terminal)
cd TripTally/frontend
npx expo start
```

### With Docker Compose

```powershell
cd TripTally/infra

# Load commands
. .\docker-commands.ps1

# Start everything
Start-Dev

# View logs
Show-Logs

# Run tests
Test-Backend

# Stop everything
Stop-Dev
```

## 🧪 Testing

### Backend Tests
```powershell
cd TripTally/backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_api_endpoint.py
```

### Frontend Tests
```powershell
cd TripTally/frontend

# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Test Results
- ✅ **229 tests passing** (100% pass rate)
- ✅ Component tests focus on rendering
- ✅ E2E tests cover complex workflows
- ✅ Service layer fully tested

## 📚 Documentation

### Main Documentation
- **Quick Start**: This file
- **Docker Deployment**: `TripTally/infra/DOCKER_DEPLOYMENT.md`
- **Docker Quick Reference**: `TripTally/infra/QUICK_REFERENCE.md`
- **API Documentation**: http://localhost:8000/docs (when running)

### Traffic Camera CI Service
- **Quick Start**: `TripTally/backend/app/services/trafficcams/docs/QUICKSTART.md`
- **Architecture**: `TripTally/backend/app/services/trafficcams/docs/ARCHITECTURE.md`
- **ML Integration**: `TripTally/backend/app/services/trafficcams/docs/ML_README.md`

### Backend Documentation
- **Backend Fixes**: `TripTally/backend/docs/`
- **API Testing**: `TripTally/backend/docs/E2E_TESTING_SUMMARY.md`
- **OAuth Setup**: `TripTally/backend/docs/GOOGLE_OAUTH_SETUP.md`

## 🔍 Troubleshooting

### Redis Connection Failed

**Problem:** Backend can't connect to Redis

**Solution:**
```powershell
# Check if Redis is running
docker ps | Select-String triptally-redis

# Start Redis if not running
docker start triptally-redis

# Or create new Redis container
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Test connection
docker exec -it triptally-redis redis-cli ping
# Should return: PONG
```

### Port Already in Use

**Problem:** Port 8000, 6379, or 19006 is already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <pid> /F

# Or change port in .env file
# BACKEND_PORT=8001
```

### Traffic CI Service Not Updating

**Problem:** CI data is stale or not updating

**Solution:**
1. Check if service is running
2. View service logs for errors
3. Verify Redis connection: `docker exec -it triptally-redis redis-cli KEYS ci:now:*`
4. Check API key in `.env`: `X_API_KEY=your_lta_key`
5. Restart service: `python simple_ci_redis.py`

### Backend Import Errors

**Problem:** Module not found errors

**Solution:**
```powershell
# Ensure virtual environment is activated
cd TripTally/backend
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 🚀 Production Deployment

For production deployment with Docker:

1. See `TripTally/infra/DOCKER_DEPLOYMENT.md`
2. Configure environment variables in `.env`
3. Use `docker-compose.yml` for production setup
4. Enable SSL/TLS with nginx
5. Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is part of SC2006 SCSI coursework.

## 👥 Team

**SC2006 SCSI Group 5**
- NTU School of Computer Science and Engineering

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Saximn/triptally/issues)
- **Documentation**: See `TripTally/infra/` and `TripTally/backend/app/services/trafficcams/docs/`

---

**⚠️ Important Notes:**
- Always configure API keys in `.env` before starting
- Redis must be running for traffic CI service
- Backend must be running before starting frontend
- For production, use strong passwords and enable SSL/TLS

**🎯 Quick Command Reference:**

```powershell
# Start Redis
docker run -d --name triptally-redis -p 6379:6379 redis:7-alpine

# Start Backend
cd TripTally/backend ; uvicorn app.main:app --reload

# Start Traffic CI
cd TripTally/backend/app/services/trafficcams ; python simple_ci_redis.py

# Start Frontend
cd TripTally/frontend ; npx expo start
```
