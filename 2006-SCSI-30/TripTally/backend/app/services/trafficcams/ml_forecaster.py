"""
ML-Powered Forecaster Strategy
Uses trained XGBoost models for multi-horizon forecasting
"""

import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import joblib
import json
from collections import deque

from .forecasting_strategy import ForecastingStrategy
from .models import CIForecast, ForecastHorizon, CIState
from .config import Config
from .logger import get_logger

logger = get_logger("ml_forecaster")


class MLForecaster(ForecastingStrategy):
    """ML-based forecasting strategy using trained XGBoost models"""
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.models: Dict[int, any] = {}
        self.scaler = None
        self.feature_cols: List[str] = []
        self.horizons: List[int] = []
        self.metadata: dict = {}
        
        # History tracking per camera
        self.ci_history: Dict[str, deque] = {}
        self.max_history = 60  # Keep 60 observations (2 hours at 2-min intervals)
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load all trained models and metadata"""
        metadata_path = self.model_dir / "ci_model_metadata.json"
        
        if not metadata_path.exists():
            logger.warning(f"No ML models found at {self.model_dir}, using fallback forecasting")
            return
        
        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            self.feature_cols = self.metadata['feature_columns']
            self.horizons = self.metadata['horizons']
            
            logger.info(f"Loading ML models for horizons: {self.horizons}")
            
            # Load scaler
            scaler_path = self.model_dir / "ci_scaler.pkl"
            self.scaler = joblib.load(scaler_path)
            logger.info("Loaded feature scaler")
            
            # Load each horizon model
            for horizon in self.horizons:
                model_path = self.model_dir / f"ci_model_xgb_{horizon}.pkl"
                if model_path.exists():
                    self.models[horizon] = joblib.load(model_path)
                    logger.info(f"Loaded model for {horizon}-minute horizon")
            
            logger.info(f"Successfully loaded {len(self.models)} ML models")
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}", exc_info=True)
            self.models = {}
    
    def _get_or_create_history(self, camera_id: str) -> deque:
        """Get history for camera, create if doesn't exist"""
        if camera_id not in self.ci_history:
            self.ci_history[camera_id] = deque(maxlen=self.max_history)
        return self.ci_history[camera_id]
    
    def _update_history(self, camera_id: str, ci_value: float):
        """Update CI history for camera"""
        history = self._get_or_create_history(camera_id)
        history.append(ci_value)
    
    def _calculate_lag_features(self, history: deque) -> dict:
        """Calculate lag features from history"""
        features = {}
        
        # Convert to list for indexing
        hist_list = list(history)
        
        # Lag features
        for lag in [1, 2, 3, 6, 12]:
            if len(hist_list) >= lag:
                features[f'CI_lag_{lag}'] = hist_list[-lag]
            else:
                features[f'CI_lag_{lag}'] = hist_list[0] if hist_list else 0.0
        
        # Rolling statistics
        if len(hist_list) >= 6:
            features['CI_roll_mean_6'] = np.mean(hist_list[-6:])
        else:
            features['CI_roll_mean_6'] = np.mean(hist_list) if hist_list else 0.0
        
        if len(hist_list) >= 12:
            features['CI_roll_mean_12'] = np.mean(hist_list[-12:])
        else:
            features['CI_roll_mean_12'] = np.mean(hist_list) if hist_list else 0.0
        
        if len(hist_list) >= 30:
            features['CI_roll_mean_30'] = np.mean(hist_list[-30:])
        else:
            features['CI_roll_mean_30'] = np.mean(hist_list) if hist_list else 0.0
        
        # Rate of change
        if len(hist_list) >= 2:
            features['CI_diff'] = hist_list[-1] - hist_list[-2]
        else:
            features['CI_diff'] = 0.0
        
        return features
    
    def _build_feature_vector(self, state: CIState) -> np.ndarray:
        """Build feature vector for prediction"""
        
        # Get history
        history = self._get_or_create_history(state.camera_id)
        
        # Calculate lag features
        lag_features = self._calculate_lag_features(history)
        
        # Build feature dict
        features = {}
        
        # Detection features
        if hasattr(state, 'veh_count'):
            features['veh_count'] = state.veh_count
        else:
            features['veh_count'] = 0
        
        if hasattr(state, 'veh_wcount'):
            features['veh_wcount'] = state.veh_wcount
        else:
            features['veh_wcount'] = 0
        
        if hasattr(state, 'area_ratio'):
            features['area_ratio'] = state.area_ratio
        else:
            features['area_ratio'] = 0.0
        
        if hasattr(state, 'motion'):
            features['motion'] = state.motion
        else:
            features['motion'] = 0.0
        
        # Temporal features
        now = datetime.now()
        features['hour'] = now.hour
        features['day_of_week'] = now.weekday()
        features['minute_of_day'] = now.hour * 60 + now.minute
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        
        # Cyclical encoding
        features['sin_t_h'] = np.sin(2 * np.pi * now.hour / 24)
        features['cos_t_h'] = np.cos(2 * np.pi * now.hour / 24)
        
        # Add lag features
        features.update(lag_features)
        
        # Build feature vector in correct order
        feature_vector = []
        for col in self.feature_cols:
            feature_vector.append(features.get(col, 0.0))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def _fallback_forecast(self, state: CIState, num_steps: int = 60) -> List[ForecastHorizon]:
        """Simple statistical forecasting as fallback"""
        history = self._get_or_create_history(state.camera_id)
        
        # Extract current CI for baseline
        current_ci = state.ci
        
        # Calculate mean and trend
        if len(history) >= 2:
            mean_ci = np.mean(history)
            recent = list(history)[-10:]
            trend = (recent[-1] - recent[0]) / len(recent) if len(recent) >= 2 else 0.0
        else:
            mean_ci = current_ci
            trend = 0.0
        
        forecasts = []
        now = datetime.now()
        
        for i in range(1, num_steps + 1):
            h = i * 2  # 2-minute intervals
            
            # Exponential decay towards mean
            decay = np.exp(-h / 60.0)
            forecast_ci = current_ci + trend * h + (1 - decay) * (mean_ci - current_ci)
            forecast_ci = max(0.0, min(1.0, forecast_ci))
            
            forecast_time = now + timedelta(minutes=h)
            
            forecasts.append(ForecastHorizon(
                horizon_minutes=h,
                predicted_ci=forecast_ci,
                confidence=0.5,  # Low confidence for simple model
                forecast_time=forecast_time
            ))
        
        return forecasts
    
    def generate_forecast(self, state: CIState) -> CIForecast:
        """Generate CI forecast using ML models or fallback"""
        
        # Update history
        self._update_history(state.camera_id, state.ci)
        
        # If no ML models, use fallback
        if not self.models:
            logger.debug(f"Using fallback forecasting for {state.camera_id}")
            forecasts = self._fallback_forecast(state, num_steps=60)
            
            return CIForecast(
                camera_id=state.camera_id,
                forecast_timestamp=datetime.now(),
                horizons=forecasts,
                model_version="fallback_v1"
            )
        
        # Use ML models
        try:
            # Build feature vector
            X = self._build_feature_vector(state)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Generate predictions for each horizon
            forecasts = []
            now = datetime.now()
            
            # All target horizons (2, 4, 6, ..., 120 minutes)
            all_horizons = list(range(2, 122, 2))
            
            for h in all_horizons:
                # Find closest trained horizon
                if h in self.models:
                    # Direct prediction
                    pred_ci = float(self.models[h].predict(X_scaled)[0])
                    confidence = 0.85
                else:
                    # Interpolate between closest horizons
                    lower = max([x for x in self.horizons if x < h], default=min(self.horizons))
                    upper = min([x for x in self.horizons if x > h], default=max(self.horizons))
                    
                    if lower == upper:
                        pred_ci = float(self.models[lower].predict(X_scaled)[0])
                        confidence = 0.85
                    else:
                        pred_lower = float(self.models[lower].predict(X_scaled)[0])
                        pred_upper = float(self.models[upper].predict(X_scaled)[0])
                        
                        # Linear interpolation
                        weight = (h - lower) / (upper - lower)
                        pred_ci = pred_lower * (1 - weight) + pred_upper * weight
                        confidence = 0.75  # Lower confidence for interpolated
                
                # Clip to valid range
                pred_ci = max(0.0, min(1.0, pred_ci))
                
                forecast_time = now + timedelta(minutes=h)
                
                forecasts.append(ForecastHorizon(
                    horizon_minutes=h,
                    predicted_ci=pred_ci,
                    confidence=confidence,
                    forecast_time=forecast_time
                ))
            
            return CIForecast(
                camera_id=state.camera_id,
                forecast_timestamp=now,
                horizons=forecasts,
                model_version=self.metadata.get('trained_at', 'ml_v1')
            )
        
        except Exception as e:
            logger.error(f"ML forecasting failed: {e}, using fallback", exc_info=True)
            fallback_forecasts = self._fallback_forecast(state, num_steps=60)
            
            return CIForecast(
                camera_id=state.camera_id,
                forecast_timestamp=datetime.now(),
                horizons=fallback_forecasts,
                model_version="fallback_v1"
            )
    
    def get_strategy_name(self) -> str:
        """Return name of the strategy (implements ForecastingStrategy)"""
        return "MLForecaster"
    
    def is_available(self) -> bool:
        """Check if strategy is available (implements ForecastingStrategy)"""
        return len(self.models) > 0


# Factory function for backwards compatibility
def create_forecaster(config: Config) -> MLForecaster:
    """Create ML forecaster instance"""
    model_dir = getattr(config, 'model_dir', './models')
    return MLForecaster(model_dir=model_dir)
