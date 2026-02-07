# TripTally CI Processing Service

A production-ready, dockerized traffic camera Congestion Index (CI) processing service built with clean architecture principles and **ML-powered forecasting**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         External Services               │
├─────────────────────────────────────────┤
│  • Singapore LTA Traffic Camera API     │
│  • Redis Cache                          │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      Application Layer (main.py)        │
├─────────────────────────────────────────┤
│  • Configuration Management             │
│  • Lifecycle Management                 │
│  • Signal Handling                      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│     Service Layer (service.py)          │
├─────────────────────────────────────────┤
│  • Orchestration                        │
│  • Error Handling                       │
│  • Metrics Collection                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      Business Logic Layer               │
├──────────────┬──────────────────────────┤
│ CI Calculator│  Forecaster              │
│ Motion Detect│  YOLO Detector           │
└──────────────┴──────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      Data Access Layer                  │
├──────────────┬──────────────────────────┤
│ API Client   │  Redis Repository        │
└──────────────┴──────────────────────────┘
```

## 📦 Components

### Core Services
- **`main.py`** - Application entry point and lifecycle management
- **`service.py`** - Main orchestrator coordinating all components
- **`config.py`** - Centralized configuration management
- **`logger.py`** - Structured logging setup

### Business Logic
- **`ci_calculator.py`** - CI calculation from detection results
- **`ml_forecaster.py`** - 🤖 **ML-powered forecasting** using XGBoost (with fallback)
- **`motion_detector.py`** - Frame differencing for motion analysis

### ML Training (New!)
- **`train_model.py`** - Complete ML training pipeline
- **`ml_forecaster.py`** - ML inference with automatic fallback
- **`analyze_data.py`** - Training data analysis
- **`quick_train.py`** - One-command training

### Data Access
- **`repository.py`** - Redis operations following Repository pattern
- **`api_client.py`** - Traffic camera API integration

### Models
- **`models.py`** - Domain entities and data structures
- **`yolo.py`** - YOLO wrapper for vehicle detection

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Navigate to service directory
cd TripTally/backend/app/services/trafficcams

# 2. Start services (Redis + CI Service)
docker-compose up -d

# 3. View logs
docker-compose logs -f ci-service

# 4. Check health
docker-compose ps

# 5. Stop services
docker-compose down
```

### Using Docker Only

```bash
# Start Redis
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Build CI service
docker build -t triptally-ci-service .

# Run CI service
docker run -d \
  --name ci-service \
  --link redis:redis \
  -e REDIS_HOST=redis \
  -v $(pwd)/models:/app/models:ro \
  triptally-ci-service
```

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
redis-server

# 3. Set environment variables (or use .env file)
export REDIS_HOST=localhost
export MODEL_PATH=models/yolov8n.pt

# 4. Run service
python main.py
```

## 🤖 ML-Powered Forecasting (NEW!)

The service now uses **machine learning** for CI prediction!

### Quick Start with ML

```bash
# 1. Analyze your training data
python analyze_data.py train/data/processed_training_data.parquet

# 2. Train ML models
python quick_train.py

# 3. Run service (automatically uses ML)
python main.py
```

**Windows PowerShell:**
```powershell
.\train.ps1
python main.py
```

### What You Get

- **XGBoost models** for 7 forecast horizons (2, 5, 10, 15, 30, 60, 120 min)
- **Automatic fallback** to statistical model if ML unavailable
- **Higher accuracy** - learns from historical patterns
- **Confidence scores** - 0.85 for ML, 0.50 for fallback

### Training Data Format

Required columns:
- `camera_id`, `ts`, `CI` (target)
- `veh_count`, `veh_wcount`, `area_ratio`, `motion`

Optional (auto-generated): temporal features, lags, rolling stats

### ML Documentation

- **[ML_README.md](ML_README.md)** - Complete ML guide
- **[ML_QUICKREF.md](ML_QUICKREF.md)** - Quick reference
- **[ML_INTEGRATION_SUMMARY.md](ML_INTEGRATION_SUMMARY.md)** - What changed

**No training data?** Service automatically uses simple statistical forecasting!

## ⚙️ Configuration

All configuration via environment variables:

### API Configuration
```bash
API_URL=https://api.data.gov.sg/v1/transport/traffic-images
X_API_KEY=your_api_key_here  # Optional
API_TIMEOUT=60
```

### Redis Configuration
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional
REDIS_TTL=600  # Key expiry in seconds
```

### Model Configuration
```bash
MODEL_PATH=models/yolov8n.pt
IMG_SIZE=640
CONF_THRES=0.25
IOU_THRES=0.45
```

### CI Parameters
```bash
K_COUNT=20       # Vehicle count normalizer
K_AREA=0.10      # Area ratio normalizer
K_MOTION=8.0     # Motion normalizer
W_DENS=0.6       # Vehicle density weight
W_AREA=0.4       # Area coverage weight
W_MREL=0.3       # Motion relief weight
W_CIRAW=0.7      # Raw CI weight
```

### Processing Configuration
```bash
LOOP_INTERVAL=120    # Seconds between runs
MAX_HISTORY=60       # Historical observations to keep
CACHE_DIR=/app/cache
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 📊 Data Structures

### Redis Keys

**Current State:** `ci:now:<camera_id>`
```json
{
  "ts": "2025-11-03T22:00:00+08:00",
  "camera_id": "1001",
  "CI": "0.67",
  "veh_count": "15",
  "veh_wcount": "18.5",
  "area_ratio": "0.045",
  "motion": "2.3",
  "model_ver": "simple_ci_v1"
}
```

**Forecast:** `ci:fcst:<camera_id>`
```json
{
  "ts": "2025-11-03T22:00:00+08:00",
  "camera_id": "1001",
  "model_ver": "simple_ci_v1",
  "h:2": "0.68",
  "h:4": "0.69",
  ...
  "h:120": "0.55"
}
```

## 🔍 Monitoring

### View Logs
```bash
# Docker Compose
docker-compose logs -f ci-service

# Docker
docker logs -f ci-service

# Local
tail -f logs/ci_service_*.log
```

### Check Redis Data
```bash
# Connect to Redis
redis-cli

# List all current states
KEYS ci:now:*

# View specific camera
HGETALL ci:now:1001

# View forecast
HGETALL ci:fcst:1001

# Monitor real-time
MONITOR
```

### Health Check
```bash
# Check if service is running
docker-compose ps

# Test Redis connection
docker exec ci-service python -c "
from repository import RedisRepository
from config import RedisConfig
repo = RedisRepository(RedisConfig.from_env())
print('Redis OK' if repo.ping() else 'Redis FAIL')
"
```

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test individual components
python -c "
from config import Config
config = Config.from_env()
config.validate()
print('Config OK')
"
```

## 📈 Performance

Typical performance metrics:
- **Image download:** ~150ms per camera
- **YOLO inference:** ~90ms per camera (CPU)
- **Total per iteration:** 60-90s for 87 cameras
- **Memory usage:** ~500MB
- **Redis storage:** ~50KB per camera

## 🔐 Security Best Practices

✅ **Implemented:**
- Non-root user in Docker
- No hardcoded secrets
- Input validation
- Error handling and logging
- Health checks

🔄 **Recommended for Production:**
- Use secrets management (e.g., Docker secrets, AWS Secrets Manager)
- Enable Redis authentication
- Use TLS for Redis connections
- Set up monitoring and alerting
- Implement rate limiting for API calls

## 🛠️ Troubleshooting

### Problem: Redis connection refused
```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Problem: YOLO model not found
```bash
# Check if model exists
ls -lh models/yolov8n.pt

# Download model if missing
# (Model should be provided separately)
```

### Problem: High memory usage
```bash
# Reduce image size
export IMG_SIZE=416  # Instead of 640

# Reduce history
export MAX_HISTORY=30  # Instead of 60
```

## 📝 Development

### Project Structure
```
trafficcams/
├── main.py                # Entry point
├── service.py             # Main orchestrator
├── config.py              # Configuration
├── logger.py              # Logging setup
├── models.py              # Domain models
├── repository.py          # Redis operations
├── api_client.py          # API client
├── ci_calculator.py       # CI calculation
├── ml_forecaster.py       # 🤖 ML forecasting
├── motion_detector.py     # Motion detection
├── yolo.py                # YOLO wrapper
├── train_model.py         # 🤖 ML training pipeline
├── analyze_data.py        # 🤖 Data analysis
├── quick_train.py         # 🤖 Quick training
├── train.ps1              # 🤖 Windows training script
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker image
├── docker-compose.yml     # Orchestration
├── README.md              # This file
├── ML_README.md           # 🤖 ML documentation
├── ML_QUICKREF.md         # 🤖 ML quick reference
└── ML_INTEGRATION_SUMMARY.md  # 🤖 ML integration guide
```

### Code Principles

1. **Separation of Concerns** - Each module has single responsibility
2. **Dependency Injection** - Components receive dependencies
3. **Clean Architecture** - Business logic independent of frameworks
4. **SOLID Principles** - Maintainable and extensible code
5. **Error Handling** - Graceful degradation and logging
6. **Configuration** - Externalized and validated

### Adding New Features

1. **New CI Feature:**
   - Add to `ci_calculator.py`
   - Update `models.py` if needed
   - Add tests

2. **New Forecast Model:**
   - Implement in `forecaster.py`
   - Keep interface compatible
   - Add configuration options

3. **New Data Source:**
   - Create new client in `api_client.py`
   - Update `service.py` orchestration
   - Add configuration

## 🚦 Deployment

### Production Checklist

- [ ] Set appropriate `LOG_LEVEL` (INFO or WARNING)
- [ ] Configure Redis persistence
- [ ] Set up monitoring and alerts
- [ ] Enable Redis authentication
- [ ] Use proper secrets management
- [ ] Set resource limits in Docker
- [ ] Configure log rotation
- [ ] Set up backups (if needed)
- [ ] Document API keys and credentials
- [ ] Test failover scenarios

### Environment-Specific Configs

**Development:**
```bash
LOG_LEVEL=DEBUG
LOOP_INTERVAL=300  # 5 min for faster iteration
```

**Staging:**
```bash
LOG_LEVEL=INFO
LOOP_INTERVAL=120
```

**Production:**
```bash
LOG_LEVEL=WARNING
LOOP_INTERVAL=120
REDIS_PASSWORD=<secure_password>
```

## 📄 License

Part of TripTally project.

## 👥 Contributors

Built with ❤️ by the TripTally team.
