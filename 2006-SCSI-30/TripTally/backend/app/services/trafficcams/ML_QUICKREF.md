# ML Forecasting Quick Reference

## 🚀 Quick Start

### Windows (PowerShell)
```powershell
# Install dependencies
pip install -r requirements.txt

# Analyze data
python analyze_data.py train\data\processed_training_data.parquet

# Train models
.\train.ps1

# Run service
python main.py
```

### Linux/Mac (Bash)
```bash
# Install dependencies
pip install -r requirements.txt

# Analyze data
python analyze_data.py train/data/processed_training_data.parquet

# Train models
make train

# Run service
python main.py
```

### Docker
```bash
# Build and start
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f ci-service

# Stop
docker-compose down
```

## 📝 Commands

| Command | Purpose |
|---------|---------|
| `python analyze_data.py <path>` | Analyze training data |
| `python train_model.py --data <path> --output <dir>` | Train ML models |
| `python quick_train.py` | Complete training pipeline |
| `.\train.ps1` (Windows) | Complete training pipeline |
| `make train` (Linux/Mac) | Complete training pipeline |
| `python main.py` | Run CI service |
| `docker-compose up` | Run with Docker |

## 📊 File Structure

```
trafficcams/
├── train/
│   └── data/
│       └── processed_training_data.parquet    # Your training data
├── models/                                     # Trained models (after training)
│   ├── ci_scaler.pkl
│   ├── ci_model_xgb_2.pkl
│   ├── ci_model_xgb_5.pkl
│   ├── ... (7 models total)
│   └── ci_model_metadata.json
├── train_model.py                              # ML training script
├── ml_forecaster.py                            # ML forecaster
├── analyze_data.py                             # Data analysis
├── quick_train.py                              # Quick training
├── train.ps1                                   # Windows training script
└── service.py                                  # Main service (uses ML)
```

## 🎯 Training Data Requirements

**Required columns:**
- `camera_id` - Camera identifier
- `ts` - Timestamp
- `CI` - Target variable (0-1)
- `veh_count` - Vehicle count
- `veh_wcount` - Weighted count
- `area_ratio` - Area ratio
- `motion` - Motion score

**Optional (auto-generated if missing):**
- `hour`, `day_of_week`, `minute_of_day`, `is_weekend`
- `sin_t_h`, `cos_t_h`
- Lag features: `CI_lag_1`, `CI_lag_2`, etc.
- Rolling means: `CI_roll_mean_6`, etc.

## 🔍 Model Output

**Files created:**
- `ci_scaler.pkl` - Feature scaler (StandardScaler)
- `ci_model_xgb_N.pkl` - XGBoost model for N-minute horizon
- `ci_model_metadata.json` - Metadata and metrics

**Horizons trained:** 2, 5, 10, 15, 30, 60, 120 minutes

**Metrics reported:**
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² (R-squared score)

## 🔧 Configuration

**Environment variables:**
```bash
MODEL_DIR=./models        # Where to find trained models
```

**In code:**
```python
from config import Config
config = Config.from_env()
config.processing.model_dir = "/path/to/models"
```

## 📈 API Changes

**Forecast response includes model version:**

```json
{
  "model_version": "2025-01-20T09:15:23"  // ML model
}
```

or

```json
{
  "model_version": "fallback_v1"  // Statistical model
}
```

**Confidence scores:**
- 0.85 = Direct ML prediction
- 0.75 = Interpolated prediction
- 0.50 = Fallback model

## ⚠️ Common Issues

### Training data not found
```bash
# Check path
ls train/data/processed_training_data.parquet

# Specify correct path
python train_model.py --data /your/path/data.parquet
```

### No ML models loaded (warning only)
```
WARNING: No ML models found at ./models, using fallback forecasting
```
**Solution:** Train models with `make train` or service will use fallback

### Import errors
```bash
# Install dependencies
pip install -r requirements.txt

# Or rebuild Docker
docker-compose build
```

### Low accuracy
- Collect more training data
- Check data quality with `analyze_data.py`
- Verify features are present
- Check for missing values

## 🎓 Understanding Forecasting

### Simple Statistical Model (Fallback)
- Persistence + mean reversion
- Uses exponential decay
- No training needed
- Confidence: 0.5

### ML Model (XGBoost)
- Gradient boosting regression
- Learns from historical patterns
- Uses 19+ features
- Separate model per horizon
- Confidence: 0.75-0.85

## 📚 Documentation

- **ML_README.md** - Complete ML documentation
- **ML_INTEGRATION_SUMMARY.md** - What changed and how to use
- **README.md** - Main project documentation
- **DEPLOYMENT.md** - Deployment guide

## 💡 Tips

1. **Start simple**: Run without ML first (fallback works!)
2. **Analyze first**: Use `analyze_data.py` to understand your data
3. **Train when ready**: Run `make train` when you have good data
4. **Monitor**: Check `model_version` in API responses
5. **Retrain regularly**: Update models with fresh data

## 🔄 Workflow

```
1. Collect Data → processed_training_data.parquet
2. Analyze → python analyze_data.py
3. Train → make train
4. Deploy → docker-compose up
5. Monitor → check logs and API responses
6. Repeat → retrain with more data
```

## ✅ Checklist

Before production:
- [ ] Training data exists and is valid
- [ ] Models trained successfully
- [ ] Service starts without errors
- [ ] API returns forecasts
- [ ] Confidence scores are reasonable
- [ ] Docker build succeeds
- [ ] Health checks pass

## 🆘 Getting Help

1. Check logs: `docker-compose logs ci-service`
2. Verify models: `ls models/`
3. Test data: `python analyze_data.py <path>`
4. Check metrics in `models/ci_model_metadata.json`

## 📞 Support

Read the docs:
- ML_README.md - Detailed ML guide
- ML_INTEGRATION_SUMMARY.md - Quick overview
- README.md - System architecture
