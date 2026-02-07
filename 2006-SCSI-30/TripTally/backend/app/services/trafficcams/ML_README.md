# ML-Powered CI Forecasting

This system uses machine learning to predict traffic congestion index (CI) for multiple time horizons (2-120 minutes ahead).

## Architecture

### Components

1. **Data Analysis** (`analyze_data.py`)
   - Analyzes training data structure
   - Shows feature distributions and correlations
   - Validates data quality

2. **Model Training** (`train_model.py`)
   - Trains XGBoost models for multiple forecast horizons
   - Creates features: lags, rolling statistics, temporal features
   - Validates using time series cross-validation
   - Saves models and metadata

3. **ML Forecaster** (`ml_forecaster.py`)
   - Loads trained models for inference
   - Builds feature vectors from current state
   - Generates forecasts with confidence scores
   - Falls back to simple statistical model if ML unavailable

4. **Integration** (`service.py`)
   - Main service uses ML forecaster automatically
   - Seamless integration with existing pipeline

## Training Data

Expected format: `train/data/processed_training_data.parquet`

Required columns:
- `camera_id`: Camera identifier
- `ts`: Timestamp
- `CI`: Target variable (0-1)
- `veh_count`: Vehicle count from YOLO
- `veh_wcount`: Weighted vehicle count
- `area_ratio`: Vehicle area ratio
- `motion`: Motion score

Optional pre-computed features:
- `hour`, `day_of_week`, `minute_of_day`, `is_weekend`
- `sin_t_h`, `cos_t_h` (cyclical time encoding)
- Lag features: `CI_lag_1`, `CI_lag_2`, etc.
- Rolling means: `CI_roll_mean_6`, etc.

## Quick Start

### 1. Analyze Training Data

```bash
python analyze_data.py train/data/processed_training_data.parquet
```

This shows:
- Dataset size and memory usage
- Column types and missing values
- Time range and camera coverage
- CI distribution and statistics
- Feature correlations
- Sample data

### 2. Train Models

```bash
python train_model.py --data train/data/processed_training_data.parquet --output ./models
```

This creates:
- `models/ci_scaler.pkl` - Feature scaler
- `models/ci_model_xgb_2.pkl` - Model for 2-minute horizon
- `models/ci_model_xgb_5.pkl` - Model for 5-minute horizon
- `models/ci_model_xgb_10.pkl` - Model for 10-minute horizon
- `models/ci_model_xgb_15.pkl` - Model for 15-minute horizon
- `models/ci_model_xgb_30.pkl` - Model for 30-minute horizon
- `models/ci_model_xgb_60.pkl` - Model for 60-minute horizon
- `models/ci_model_xgb_120.pkl` - Model for 120-minute horizon
- `models/ci_model_metadata.json` - Model metadata and metrics

### 3. Run Service with ML

The service automatically uses ML models if available:

```bash
python main.py
```

Logs will show:
```
Loading ML models for horizons: [2, 5, 10, 15, 30, 60, 120]
Loaded model for 2-minute horizon
Loaded model for 5-minute horizon
...
Successfully loaded 7 ML models
```

### 4. Docker with ML

Update `docker-compose.yml` to mount models:

```yaml
services:
  ci-service:
    volumes:
      - ./models:/app/models:ro
```

Then:

```bash
docker-compose build
docker-compose up
```

## ML Model Details

### Training Process

1. **Feature Engineering**
   - Lag features: CI at t-1, t-2, t-3, t-6, t-12 intervals
   - Rolling statistics: mean over 6, 12, 30 observations
   - Temporal features: hour, day of week, cyclical encoding
   - Rate of change: CI difference

2. **Model Selection**
   - XGBoost Regressor (gradient boosting)
   - Separate model for each horizon
   - Time series cross-validation (3 folds)
   - Early stopping on validation set

3. **Hyperparameters**
   - n_estimators: 100
   - max_depth: 6
   - learning_rate: 0.1
   - subsample: 0.8
   - colsample_bytree: 0.8

### Inference

1. **Feature Building**
   - Extract current state features
   - Calculate lags from history buffer
   - Compute rolling statistics
   - Add temporal features

2. **Prediction**
   - Scale features using trained scaler
   - Get prediction from appropriate horizon model
   - Interpolate for intermediate horizons
   - Clip to valid range [0, 1]

3. **Confidence Scores**
   - 0.85 for direct model predictions
   - 0.75 for interpolated predictions
   - 0.50 for fallback statistical model

### Fallback Behavior

If ML models are unavailable:
- Uses simple persistence + mean reversion
- Lower confidence scores
- Still provides reasonable forecasts
- No training data required

## Performance Metrics

Training output shows:
```
2min - RMSE: 0.0842, MAE: 0.0623, R²: 0.7231
5min - RMSE: 0.0951, MAE: 0.0712, R²: 0.6834
10min - RMSE: 0.1123, MAE: 0.0845, R²: 0.6201
...
```

- **RMSE**: Root Mean Squared Error (lower is better)
- **MAE**: Mean Absolute Error (lower is better)
- **R²**: R-squared score (higher is better, max 1.0)

## Updating Models

To retrain with new data:

1. Collect more data to `processed_training_data.parquet`
2. Run training: `python train_model.py`
3. Restart service or rebuild Docker

Models are versioned by training timestamp in metadata.

## API Usage

Forecasts include model version:

```json
{
  "camera_id": "1001",
  "current_ci": 0.45,
  "forecast_time": "2025-01-20T10:30:00",
  "forecasts": [
    {
      "minutes_ahead": 2,
      "forecast_ci": 0.48,
      "confidence": 0.85,
      "forecast_time": "2025-01-20T10:32:00"
    }
  ],
  "model_version": "2025-01-20T09:15:23"
}
```

Check `model_version`:
- ISO timestamp: ML model
- "fallback_v1": Statistical model

## Troubleshooting

### No ML models loaded

```
WARNING: No ML models found at ./models, using fallback forecasting
```

Solution: Run `python train_model.py` first

### Import errors

```
ModuleNotFoundError: No module named 'xgboost'
```

Solution: `pip install -r requirements.txt`

### Training data not found

```
FileNotFoundError: Training data not found: train/data/processed_training_data.parquet
```

Solution: Check path or specify with `--data` argument

### Low accuracy

- Collect more training data
- Check for missing features
- Verify data quality with `analyze_data.py`
- Consider different model hyperparameters

## Advanced Configuration

Set model directory in environment:

```bash
export MODEL_DIR=/path/to/models
python main.py
```

Or in code:

```python
from config import Config
config = Config.from_env()
config.processing.model_dir = "/path/to/models"
```

## Future Enhancements

- [ ] LSTM/GRU models for sequential patterns
- [ ] Ensemble multiple model types
- [ ] Online learning / incremental updates
- [ ] Per-camera model specialization
- [ ] Attention mechanisms for important features
- [ ] AutoML for hyperparameter optimization
