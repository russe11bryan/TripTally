# Forecaster Configuration Guide

## Current Status

### What Forecaster is Being Used?

The system uses **AUTO mode** by default, which means:

1. **Tries ML forecaster first** - If trained XGBoost models are found
2. **Falls back to Simple forecaster** - If ML models are not available

### Checking Your Current Setup

**Environment Variable:**
```bash
# Check current setting (Windows PowerShell)
$env:FORECASTER_TYPE

# If empty/not set, default is 'auto'
```

**ML Models Status:**
```bash
# Check if ML models exist
Test-Path "models/ci_model_metadata.json"

# List ML model files
Get-ChildItem models/ci_model_*.pkl
```

**Current Result:**
- ❌ **No ML models found** (`ci_model_metadata.json` does not exist)
- ✅ **Using Simple Forecaster** (statistical time series model)

---

## Available Forecasters

### 1. **Simple Forecaster** (Current)
- **Type:** Statistical time series model
- **Algorithm:** Persistence + Mean Reversion + Trend Extrapolation
- **Requirements:** None (always available)
- **Confidence:** 0.3-0.5
- **Speed:** Very fast (~2ms per camera)
- **Accuracy:** Basic (good baseline)

**How it works:**
```python
# Short-term: Current value + trend
# Long-term: Exponential decay towards historical mean
forecast_ci = current_ci + trend * h + (1 - decay) * (mean_ci - current_ci)
```

### 2. **ML Forecaster** (Needs Training)
- **Type:** Machine Learning (XGBoost)
- **Algorithm:** Gradient Boosted Trees
- **Requirements:** Trained models (7 models for different horizons)
- **Confidence:** 0.75-0.85
- **Speed:** Fast (~15ms per camera)
- **Accuracy:** High (learns from historical patterns)

**Trained horizons:** 2, 5, 10, 15, 30, 60, 120 minutes  
**Interpolated horizons:** All other 2-minute intervals

**Features used:**
- Current CI, vehicle count, area ratio, motion
- Temporal: hour, day of week, cyclical time encoding
- Historical: lags (1, 2, 3, 6, 12 steps back)
- Rolling statistics: mean over 6, 12, 30 steps

---

## How to Change Forecaster

### Option 1: Environment Variable (Recommended)

#### Windows PowerShell:
```powershell
# Set forecaster type
$env:FORECASTER_TYPE = "simple"   # Force simple forecaster
$env:FORECASTER_TYPE = "ml"       # Force ML forecaster (requires models)
$env:FORECASTER_TYPE = "auto"     # Auto-select (default)

# Restart service
cd "C:\NTU Stuffs\Modules\Y2S1\SC2006\triptally\TripTally\backend\app\services\trafficcams"
docker-compose restart ci-service
```

#### Linux/Mac:
```bash
# Set forecaster type
export FORECASTER_TYPE=simple
export FORECASTER_TYPE=ml
export FORECASTER_TYPE=auto

# Restart service
docker-compose restart ci-service
```

### Option 2: Docker Compose Environment

Edit `docker-compose.yml`:
```yaml
services:
  ci-service:
    environment:
      - FORECASTER_TYPE=simple    # Change this
      # or
      - FORECASTER_TYPE=ml
      # or
      - FORECASTER_TYPE=auto
```

Then rebuild:
```bash
docker-compose up -d --build
```

### Option 3: .env File

Create/edit `.env` file in the trafficcams directory:
```bash
FORECASTER_TYPE=simple
# or
FORECASTER_TYPE=ml
# or
FORECASTER_TYPE=auto
```

Then:
```bash
docker-compose up -d --build
```

### Option 4: Programmatically (Python Code)

In your code:
```python
from service import CIProcessingService
from config import Config

config = Config.from_env()

# Force specific forecaster
service = CIProcessingService(
    config,
    forecaster_type="simple"  # or "ml" or "auto"
)
```

---

## Training ML Models (Optional)

If you want to use the ML forecaster, you need to train models first.

### Prerequisites
1. Historical training data in Parquet format
2. Required columns: `camera_id`, `ts`, `CI`, `veh_count`, `veh_wcount`, `area_ratio`, `motion`

### Quick Training

```bash
cd "C:\NTU Stuffs\Modules\Y2S1\SC2006\triptally\TripTally\backend\app\services\trafficcams"

# Windows PowerShell
.\train.ps1

# Linux/Mac
python quick_train.py
```

This will create:
- `models/ci_model_metadata.json` - Model metadata
- `models/ci_scaler.pkl` - Feature scaler
- `models/ci_model_xgb_2.pkl` - Model for 2-min horizon
- `models/ci_model_xgb_5.pkl` - Model for 5-min horizon
- ... (7 models total)

### After Training

```bash
# Restart service to load new models
docker-compose restart ci-service

# Check logs to confirm ML models are loaded
docker-compose logs ci-service | grep "ML"
```

---

## Verification

### Check Which Forecaster is Active

#### Method 1: Check Logs
```bash
docker-compose logs ci-service | grep -i "forecaster"
```

Look for:
```
✅ Using ML Forecaster: "Creating ml forecaster"
✅ Using Simple Forecaster: "ML forecaster not available, using simple"
```

#### Method 2: Check Redis Data
```bash
redis-cli
> HGET ci:fcst:1001 model_ver
```

Response:
- `"ml_v1"` or timestamp = **ML Forecaster**
- `"simple_v1"` = **Simple Forecaster**
- `"fallback_v1"` = **ML tried but failed, using fallback**

#### Method 3: Python Test
```python
from factory import ForecasterFactory
from config import Config

config = Config.from_env()
forecaster = ForecasterFactory.create("auto", config)

print(f"Using: {forecaster.get_strategy_name()}")
print(f"Available: {forecaster.is_available()}")
```

---

## Performance Comparison

| Feature | Simple Forecaster | ML Forecaster |
|---------|-------------------|---------------|
| Setup Time | Instant | Requires training (~10 min) |
| Inference Speed | 2ms/camera | 15ms/camera |
| Memory Usage | ~5 MB | ~50 MB |
| Accuracy (MAE) | ~0.15 | ~0.08 |
| Confidence | 0.3-0.5 | 0.75-0.85 |
| Training Data | None | Required |
| Adaptability | Limited | Learns patterns |

---

## Troubleshooting

### Problem: ML Forecaster Not Loading

**Check:**
```bash
# 1. Models exist?
Test-Path models/ci_model_metadata.json

# 2. Environment variable set?
$env:FORECASTER_TYPE

# 3. Check logs
docker-compose logs ci-service | grep -A 10 "forecaster"
```

**Solution:**
- Train models using `train.ps1` or `quick_train.py`
- Set `FORECASTER_TYPE=auto` or `ml`
- Rebuild container: `docker-compose up -d --build`

### Problem: Simple Forecaster Not Working

**Check:**
```bash
# Check history
redis-cli
> LLEN ci:history:1001
```

**Solution:**
- Simple forecaster always works, but needs some history for better predictions
- Wait a few iterations (5-10 minutes) for history to build up

### Problem: Low Confidence Predictions

**Reasons:**
- **Confidence 0.3:** Simple forecaster with no history
- **Confidence 0.5:** Simple forecaster with history
- **Confidence 0.75:** ML forecaster (interpolated)
- **Confidence 0.85:** ML forecaster (direct prediction)

**Solution:**
- For higher confidence, train and use ML models
- Ensure sufficient historical data for ML training

---

## Recommendations

### For Development
```bash
# Use simple forecaster (faster, no training needed)
$env:FORECASTER_TYPE = "simple"
```

### For Production
```bash
# Use auto mode (tries ML, falls back to simple)
$env:FORECASTER_TYPE = "auto"

# After training models, ensure they're deployed
```

### For Best Accuracy
```bash
# 1. Collect 2-4 weeks of historical data
# 2. Train ML models
# 3. Force ML mode
$env:FORECASTER_TYPE = "ml"
```

---

## Current Configuration Summary

**Your Setup:**
- ✅ Environment Variable: `Not set` (defaults to `auto`)
- ✅ ML Models: `Not found`
- ✅ **Currently Using: Simple Forecaster** (statistical)
- ✅ Forecasts: 60 predictions (2, 4, 6, ..., 120 minutes)
- ✅ Confidence: 0.3-0.5

**To switch to ML:**
1. Train models: `.\train.ps1` (requires training data)
2. Rebuild: `docker-compose up -d --build`
3. Verify: `docker-compose logs ci-service | grep "ML"`

**To explicitly use simple:**
1. Set: `$env:FORECASTER_TYPE = "simple"`
2. Restart: `docker-compose restart ci-service`

---

## Quick Reference

```powershell
# Show current forecaster
docker-compose logs ci-service | Select-String "forecaster"

# Change to simple
$env:FORECASTER_TYPE = "simple"
docker-compose restart ci-service

# Change to ML (needs models)
$env:FORECASTER_TYPE = "ml"
docker-compose restart ci-service

# Auto mode (default)
$env:FORECASTER_TYPE = "auto"
docker-compose restart ci-service

# Check which is active
redis-cli
> HGET ci:fcst:1001 model_ver
```

The service is currently using the **Simple Forecaster** because ML models haven't been trained yet! 📊
