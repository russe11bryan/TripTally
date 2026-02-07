# Design Patterns Implementation

This document explains the design patterns used in the CI forecasting system to provide flexibility and maintainability.

## Overview

The system uses three main design patterns:
1. **Strategy Pattern** - For forecasting algorithms
2. **Repository Pattern** - For data persistence
3. **Factory Pattern** - For creating implementations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CIProcessingService                         │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  ServiceContext   │      │   Factories      │        │
│  │  ┌─────────────┐ │      │  ┌────────────┐  │        │
│  │  │ Repository  │ │◄─────┤  │Repository  │  │        │
│  │  │  Strategy   │ │      │  │Factory     │  │        │
│  │  └─────────────┘ │      │  └────────────┘  │        │
│  │  ┌─────────────┐ │      │  ┌────────────┐  │        │
│  │  │ Forecasting │ │◄─────┤  │Forecaster  │  │        │
│  │  │  Strategy   │ │      │  │Factory     │  │        │
│  │  └─────────────┘ │      │  └────────────┘  │        │
│  └──────────────────┘      └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
              │                        │
              │                        │
    ┌─────────┴────────────┐  ┌───────┴────────────┐
    │  Data Repositories   │  │  Forecasters       │
    ├──────────────────────┤  ├────────────────────┤
    │ • RedisRepository    │  │ • SimpleForecaster │
    │ • CSVRepository      │  │ • MLForecaster     │
    │ • SQLRepository      │  │ • (Future: LSTM)   │
    └──────────────────────┘  └────────────────────┘
```

## 1. Strategy Pattern (Forecasting)

### Interface: `ForecastingStrategy`

```python
from forecasting_strategy import ForecastingStrategy
from models import CIState, CIForecast

class MyCustomForecaster(ForecastingStrategy):
    def generate_forecast(self, state: CIState) -> CIForecast:
        # Your forecasting logic here
        pass
    
    def get_strategy_name(self) -> str:
        return "MyCustomForecaster"
    
    def is_available(self) -> bool:
        return True  # Check if strategy can be used
```

### Available Implementations

#### SimpleForecaster
- Statistical persistence + mean reversion
- No training required
- Always available
- Confidence: 0.5

```python
from forecaster import SimpleForecaster

forecaster = SimpleForecaster(max_history=60)
forecast = forecaster.generate_forecast(ci_state)
```

#### MLForecaster
- XGBoost-based machine learning
- Requires trained models
- Higher accuracy
- Confidence: 0.75-0.85

```python
from ml_forecaster import MLForecaster

forecaster = MLForecaster(model_dir="./models")
if forecaster.is_available():
    forecast = forecaster.generate_forecast(ci_state)
```

### Switching Forecasters

```python
from factory import ForecasterFactory, ForecasterType

# Create specific forecaster
simple = ForecasterFactory.create(ForecasterType.SIMPLE, config)
ml = ForecasterFactory.create(ForecasterType.ML, config)

# Auto-select (tries ML first, falls back to simple)
auto = ForecasterFactory.create(ForecasterType.AUTO, config)
```

## 2. Repository Pattern (Data Storage)

### Interface: `DataRepository`

```python
from data_repository import DataRepository
from models import CIState, CIForecast, Camera

class MyCustomRepository(DataRepository):
    def save_ci_state(self, state: CIState) -> bool:
        # Save implementation
        pass
    
    def get_ci_state(self, camera_id: str) -> Optional[CIState]:
        # Retrieve implementation
        pass
    
    # ... implement all methods
    
    def get_repository_name(self) -> str:
        return "MyCustom"
```

### Available Implementations

#### RedisRepository
- In-memory cache
- Fast access
- Automatic TTL
- Best for production

```python
from repository import RedisRepository
from config import Config

config = Config.from_env()
repo = RedisRepository(config.redis)
repo.save_ci_state(state)
```

#### CSVRepository
- File-based storage
- Good for analysis/export
- Thread-safe
- Best for development/testing

```python
from csv_repository import CSVRepository

repo = CSVRepository(base_dir="./data")
repo.save_ci_state(state)
```

#### SQLRepository
- SQLite database
- Queryable history
- Indexed queries
- Best for analytics

```python
from sql_repository import SQLRepository

repo = SQLRepository(db_path="./data/traffic.db")
repo.save_ci_state(state)
```

### Switching Repositories

```python
from factory import RepositoryFactory, RepositoryType

# Create specific repository
redis = RepositoryFactory.create(RepositoryType.REDIS, config)
csv = RepositoryFactory.create(RepositoryType.CSV, config)
sql = RepositoryFactory.create(RepositoryType.SQL, config)
```

## 3. Factory Pattern (Creation)

### ServiceContext

The `ServiceContext` combines repository and forecaster:

```python
from factory import ServiceContext

# Create from config (reads REPOSITORY_TYPE and FORECASTER_TYPE)
context = ServiceContext.from_config(config)

# Or specify explicitly
context = ServiceContext.from_config(
    config,
    repo_type="redis",
    forecaster_type="ml"
)

# Access components
repository = context.repository
forecaster = context.forecaster

# Switch implementations at runtime
context.switch_repository("csv")
context.switch_forecaster("simple")
```

## Configuration

### Environment Variables

```bash
# Repository selection
REPOSITORY_TYPE=redis   # redis, csv, sql
DATA_DIR=./data        # For CSV repository
DB_PATH=./data/ci.db   # For SQL repository

# Forecaster selection
FORECASTER_TYPE=auto   # auto, simple, ml
MODEL_DIR=./models     # For ML forecaster

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### In Code

```python
from config import Config

config = Config.from_env()

# Override if needed
config.processing.repository_type = "csv"
config.processing.forecaster_type = "ml"
```

## Usage Examples

### Example 1: Production Setup (Redis + ML)

```python
from config import Config
from service import CIProcessingService

config = Config.from_env()
service = CIProcessingService(
    config,
    repo_type="redis",
    forecaster_type="auto"  # Uses ML if available
)

service.run_loop()
```

### Example 2: Development Setup (CSV + Simple)

```python
from config import Config
from service import CIProcessingService

config = Config.from_env()
service = CIProcessingService(
    config,
    repo_type="csv",
    forecaster_type="simple"
)

service.process_all_cameras()
```

### Example 3: Analytics Setup (SQL + ML)

```python
from config import Config
from service import CIProcessingService

config = Config.from_env()
service = CIProcessingService(
    config,
    repo_type="sql",
    forecaster_type="ml"
)

# Process and store in database for analysis
service.process_all_cameras()
```

### Example 4: Switching at Runtime

```python
from config import Config
from service import CIProcessingService

config = Config.from_env()
service = CIProcessingService(config)

# Start with Redis + ML
print(f"Using {service.repository.get_repository_name()}")
print(f"Using {service.forecaster.get_strategy_name()}")

# Switch to CSV for export
service.context.switch_repository("csv")

# Switch to simple forecaster if ML fails
if not service.forecaster.is_available():
    service.context.switch_forecaster("simple")
```

## Adding New Implementations

### Adding a New Forecaster

1. Create class implementing `ForecastingStrategy`:

```python
# my_forecaster.py
from forecasting_strategy import ForecastingStrategy
from models import CIState, CIForecast

class LSTMForecaster(ForecastingStrategy):
    def __init__(self, model_path: str):
        self.model = load_lstm_model(model_path)
    
    def generate_forecast(self, state: CIState) -> CIForecast:
        # LSTM forecasting logic
        pass
    
    def get_strategy_name(self) -> str:
        return "LSTMForecaster"
    
    def is_available(self) -> bool:
        return self.model is not None
```

2. Add to `ForecasterFactory`:

```python
# factory.py
class ForecasterType(Enum):
    # ... existing
    LSTM = "lstm"

class ForecasterFactory:
    @staticmethod
    def create(forecaster_type, config):
        # ... existing cases
        elif forecaster_type == ForecasterType.LSTM:
            from my_forecaster import LSTMForecaster
            model_path = config.processing.lstm_model_path
            return LSTMForecaster(model_path)
```

3. Use it:

```python
service = CIProcessingService(config, forecaster_type="lstm")
```

### Adding a New Repository

1. Create class implementing `DataRepository`:

```python
# postgres_repository.py
from data_repository import DataRepository
import psycopg2

class PostgresRepository(DataRepository):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def save_ci_state(self, state: CIState) -> bool:
        # PostgreSQL save logic
        pass
    
    # ... implement all methods
    
    def get_repository_name(self) -> str:
        return "PostgreSQL"
```

2. Add to `RepositoryFactory`:

```python
# factory.py
class RepositoryType(Enum):
    # ... existing
    POSTGRES = "postgres"

class RepositoryFactory:
    @staticmethod
    def create(repo_type, config):
        # ... existing cases
        elif repo_type == RepositoryType.POSTGRES:
            from postgres_repository import PostgresRepository
            conn_str = config.processing.postgres_connection_string
            return PostgresRepository(conn_str)
```

3. Use it:

```python
service = CIProcessingService(config, repo_type="postgres")
```

## Benefits

### 1. Flexibility
- Switch between implementations without code changes
- Configure via environment variables
- Runtime switching supported

### 2. Testability
- Easy to create mock implementations
- Test with CSV/SQLite in development
- No Redis dependency for unit tests

### 3. Maintainability
- Clear interfaces
- Single Responsibility Principle
- Open/Closed Principle (open for extension, closed for modification)

### 4. Extensibility
- Add new forecasters without changing existing code
- Add new repositories without breaking existing ones
- Easy to experiment with new approaches

## Testing

### Mock Repository

```python
from data_repository import DataRepository

class MockRepository(DataRepository):
    def __init__(self):
        self.states = {}
        self.forecasts = {}
    
    def save_ci_state(self, state: CIState) -> bool:
        self.states[state.camera_id] = state
        return True
    
    def get_ci_state(self, camera_id: str):
        return self.states.get(camera_id)
    
    # ... implement rest
```

### Unit Test

```python
def test_service():
    mock_repo = MockRepository()
    mock_forecaster = SimpleForecaster()
    
    context = ServiceContext(mock_repo, mock_forecaster)
    service = CIProcessingService(config)
    service.context = context
    
    # Test without real Redis or ML models
    service.process_camera(camera_data)
    
    assert len(mock_repo.states) > 0
```

## Best Practices

1. **Always program to the interface** - Use `DataRepository` and `ForecastingStrategy` types
2. **Use factories for creation** - Don't instantiate implementations directly
3. **Configure via environment** - Makes deployment flexible
4. **Check availability** - Use `is_available()` before using forecasters
5. **Handle failures gracefully** - Implement fallbacks

## Summary

The design patterns provide:
- ✅ Easy switching between Redis/CSV/SQL storage
- ✅ Easy switching between Simple/ML forecasters
- ✅ Runtime configuration
- ✅ Testability without dependencies
- ✅ Extensibility for new implementations
- ✅ Clean, maintainable code

Use `ServiceContext.from_config()` for simple setup, or create specific implementations for fine-grained control.
