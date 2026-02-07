# Design Patterns Quick Reference

## 🎯 Quick Setup

### Environment Variables
```bash
export REPOSITORY_TYPE=redis    # redis, csv, sql
export FORECASTER_TYPE=auto     # simple, ml, auto
```

### In Code
```python
from config import Config
from service import CIProcessingService

config = Config.from_env()
service = CIProcessingService(config)
# Uses REPOSITORY_TYPE and FORECASTER_TYPE from environment
```

## 📦 Repository Pattern

### Available Implementations
| Type | Class | Best For |
|------|-------|----------|
| `redis` | `RedisRepository` | Production |
| `csv` | `CSVRepository` | Development/Export |
| `sql` | `SQLRepository` | Analytics |

### Usage
```python
# Method 1: Via config
export REPOSITORY_TYPE=csv
service = CIProcessingService(config)

# Method 2: Explicit
service = CIProcessingService(config, repo_type="csv")

# Method 3: Factory
from factory import RepositoryFactory
repo = RepositoryFactory.create("csv", config)

# Method 4: Runtime switch
service.context.switch_repository("sql")
```

## 🔮 Forecasting Pattern

### Available Implementations
| Type | Class | Confidence | Requires |
|------|-------|------------|----------|
| `simple` | `SimpleForecaster` | 0.5 | Nothing |
| `ml` | `MLForecaster` | 0.75-0.85 | Trained models |
| `auto` | Auto-select | Varies | Nothing |

### Usage
```python
# Method 1: Via config
export FORECASTER_TYPE=ml
service = CIProcessingService(config)

# Method 2: Explicit
service = CIProcessingService(config, forecaster_type="ml")

# Method 3: Factory
from factory import ForecasterFactory
forecaster = ForecasterFactory.create("ml", config)

# Method 4: Runtime switch
service.context.switch_forecaster("simple")
```

## 🏭 Factory Pattern

### RepositoryFactory
```python
from factory import RepositoryFactory, RepositoryType

# String
repo = RepositoryFactory.create("redis", config)

# Enum
repo = RepositoryFactory.create(RepositoryType.CSV, config)
```

### ForecasterFactory
```python
from factory import ForecasterFactory, ForecasterType

# String
forecaster = ForecasterFactory.create("auto", config)

# Enum
forecaster = ForecasterFactory.create(ForecasterType.ML, config)
```

### ServiceContext
```python
from factory import ServiceContext

# Auto from config
context = ServiceContext.from_config(config)

# Explicit
context = ServiceContext.from_config(
    config,
    repo_type="csv",
    forecaster_type="ml"
)

# Access components
repo = context.repository
forecaster = context.forecaster

# Switch at runtime
context.switch_repository("sql")
context.switch_forecaster("simple")
```

## 🔧 Common Patterns

### Production Setup
```python
# Redis + ML (auto-fallback)
service = CIProcessingService(
    config,
    repo_type="redis",
    forecaster_type="auto"
)
```

### Development Setup
```python
# CSV + Simple (no dependencies)
service = CIProcessingService(
    config,
    repo_type="csv",
    forecaster_type="simple"
)
```

### Analytics Setup
```python
# SQL + ML (queryable history)
service = CIProcessingService(
    config,
    repo_type="sql",
    forecaster_type="ml"
)
```

## 🧪 Testing

### Mock Repository
```python
from data_repository import DataRepository

class MockRepository(DataRepository):
    def __init__(self):
        self.data = {}
    
    def save_ci_state(self, state):
        self.data[state.camera_id] = state
        return True
    
    # ... implement rest

# Use in tests
mock_repo = MockRepository()
service.context.repository = mock_repo
```

### Test Without Redis
```bash
export REPOSITORY_TYPE=csv
python -m pytest tests/
```

### Test Without ML Models
```bash
export FORECASTER_TYPE=simple
python main.py
```

## 📊 Checking Current Implementation

```python
# What repository?
print(service.repository.get_repository_name())
# Output: "Redis" or "CSV" or "SQLite"

# What forecaster?
print(service.forecaster.get_strategy_name())
# Output: "SimpleForecaster" or "MLForecaster"

# Is forecaster available?
if service.forecaster.is_available():
    print("Can use this forecaster")
```

## 🔄 Runtime Switching

```python
# Start with Redis + ML
service = CIProcessingService(config)

# Process some cameras
service.process_camera(camera1)

# Switch to CSV for export
service.context.switch_repository("csv")
service.process_camera(camera2)  # Now saves to CSV

# Switch to simple forecaster
service.context.switch_forecaster("simple")
forecast = service.forecaster.generate_forecast(state)
```

## 🆕 Adding New Implementations

### New Forecaster
```python
# 1. Create class
from forecasting_strategy import ForecastingStrategy

class MyForecaster(ForecastingStrategy):
    def generate_forecast(self, state):
        # Your logic
        pass
    
    def get_strategy_name(self):
        return "MyForecaster"
    
    def is_available(self):
        return True

# 2. Add to ForecasterFactory in factory.py

# 3. Use it
service = CIProcessingService(config, forecaster_type="my")
```

### New Repository
```python
# 1. Create class
from data_repository import DataRepository

class MyRepository(DataRepository):
    def save_ci_state(self, state):
        # Your logic
        return True
    
    # ... implement all methods
    
    def get_repository_name(self):
        return "MyRepo"

# 2. Add to RepositoryFactory in factory.py

# 3. Use it
service = CIProcessingService(config, repo_type="my")
```

## 🎭 Interface Methods

### DataRepository Interface
```python
save_ci_state(state: CIState) -> bool
get_ci_state(camera_id: str) -> Optional[CIState]
save_forecast(forecast: CIForecast) -> bool
get_forecast(camera_id: str) -> Optional[CIForecast]
save_camera_metadata(camera: Camera) -> bool
get_camera_metadata(camera_id: str) -> Optional[Camera]
list_cameras() -> List[str]
health_check() -> bool
get_repository_name() -> str
```

### ForecastingStrategy Interface
```python
generate_forecast(state: CIState) -> CIForecast
get_strategy_name() -> str
is_available() -> bool
```

## 📝 Configuration Variables

| Variable | Options | Default |
|----------|---------|---------|
| `REPOSITORY_TYPE` | redis, csv, sql | redis |
| `FORECASTER_TYPE` | simple, ml, auto | auto |
| `MODEL_DIR` | path | ./models |
| `DATA_DIR` | path | ./data |
| `DB_PATH` | path | ./data/traffic_ci.db |
| `REDIS_HOST` | hostname | localhost |
| `REDIS_PORT` | port | 6379 |

## 🚀 Docker Configuration

```yaml
# docker-compose.yml
environment:
  - REPOSITORY_TYPE=redis
  - FORECASTER_TYPE=auto
  - MODEL_DIR=/app/models
  - DATA_DIR=/app/data
```

## 🎓 Examples

### Example 1: CSV Export
```python
# Process with Redis, then export to CSV
service = CIProcessingService(config, repo_type="redis")
service.process_all_cameras()

# Switch to CSV
service.context.switch_repository("csv")
service.process_all_cameras()  # Now also in CSV
```

### Example 2: Fallback Forecaster
```python
# Try ML, fallback to simple
service = CIProcessingService(config, forecaster_type="auto")

if not service.forecaster.is_available():
    print("Using fallback forecaster")
```

### Example 3: Development Testing
```python
# Test locally without Redis
export REPOSITORY_TYPE=csv
export FORECASTER_TYPE=simple

python main.py
```

## 📚 Documentation

- **DESIGN_PATTERNS.md** - Complete guide
- **DESIGN_PATTERNS_COMPLETE.md** - Implementation summary
- **demo_patterns.py** - Working examples

## ✅ Checklist

Before deployment:
- [ ] Set REPOSITORY_TYPE
- [ ] Set FORECASTER_TYPE
- [ ] Configure MODEL_DIR (if using ML)
- [ ] Test health checks
- [ ] Verify implementations work

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Redis connection refused" | Use `REPOSITORY_TYPE=csv` |
| "No ML models found" | Use `FORECASTER_TYPE=simple` |
| "Cannot import X" | Check file exists, install deps |
| "Unknown repository type" | Check spelling in config |

## 💡 Tips

1. Use `auto` forecaster type - tries ML, falls back to simple
2. Use CSV repository for development (no Redis needed)
3. Use SQL repository for analytics (queryable history)
4. Check `is_available()` before using forecaster
5. Use factories for consistent creation
6. Program to interfaces, not implementations

---

**Quick Start:** `export REPOSITORY_TYPE=csv FORECASTER_TYPE=auto && python main.py`
