"""
Simple Forecaster Strategy
Generates CI predictions using statistical time series model
"""

import math
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict

from .forecasting_strategy import ForecastingStrategy
from .models import ForecastHorizon, CIForecast, CIState
from .logger import get_logger

logger = get_logger("simple_forecaster")


class SimpleForecaster(ForecastingStrategy):
    """Simple statistical forecasting strategy (persistence + mean reversion)"""
    
    def __init__(self, max_history: int = 60):
        self.max_history = max_history
        # Store history per camera: camera_id -> deque of (timestamp, CI)
        self.history = {}
    
    def add_observation(self, camera_id: str, timestamp: datetime, ci_value: float) -> None:
        """Add new CI observation to history"""
        if camera_id not in self.history:
            self.history[camera_id] = deque(maxlen=self.max_history)
        
        self.history[camera_id].append((timestamp, ci_value))
        logger.debug(f"Added observation for {camera_id}, history size: {len(self.history[camera_id])}")
    
    def generate_forecast(self, state: CIState) -> CIForecast:
        """
        Generate forecast for multiple horizons (implements ForecastingStrategy)
        
        Uses simple persistence + mean reversion model:
        - Short term: Current value + trend
        - Long term: Exponential decay to historical mean
        
        Args:
            state: Current CI state
            
        Returns:
            CIForecast object with predictions
        """
        camera_id = state.camera_id
        # Extract current CI
        current_ci = state.ci
        timestamp = state.timestamp
        horizons_min = list(range(2, 121, 2))  # 2, 4, 6, ..., 120 minutes
        forecast_points = []
        
        history = self.history.get(camera_id, deque())
        
        if len(history) < 2:
            # Insufficient history - use persistence (current value)
            logger.debug(f"Using persistence model for {camera_id} (history: {len(history)})")
            for h in horizons_min:
                forecast_points.append(ForecastHorizon(
                    horizon_minutes=h,
                    predicted_ci=current_ci,
                    confidence=0.3,
                    forecast_time=timestamp + timedelta(minutes=h)
                ))
        else:
            # Calculate statistics from history
            recent_cis = [ci for _, ci in list(history)[-30:]]  # Last 30 observations
            mean_ci = float(np.mean(recent_cis))
            
            # Calculate trend from recent observations
            recent_10 = [ci for _, ci in list(history)[-10:]]
            trend = 0.0
            if len(recent_10) >= 2:
                trend = (recent_10[-1] - recent_10[0]) / len(recent_10)
            
            logger.debug(f"Forecasting for {camera_id}: mean={mean_ci:.3f}, trend={trend:.4f}")
            
            # Generate forecasts for each horizon
            for h in horizons_min:
                # Decay factor: stronger decay for longer horizons
                # 60-minute half-life
                decay = math.exp(-h / 60.0)
                
                # Forecast combines:
                # 1. Current value (baseline)
                # 2. Trend extrapolation
                # 3. Mean reversion (stronger for longer horizons)
                forecast_ci = (
                    current_ci +
                    trend * h +
                    (1 - decay) * (mean_ci - current_ci)
                )
                
                # Clip to valid range
                forecast_ci = max(0.0, min(1.0, forecast_ci))
                
                forecast_points.append(ForecastHorizon(
                    horizon_minutes=h,
                    predicted_ci=forecast_ci,
                    confidence=0.5,  # Lower confidence for simple model
                    forecast_time=timestamp + timedelta(minutes=h)
                ))
        
        return CIForecast(
            camera_id=camera_id,
            forecast_timestamp=timestamp,
            horizons=forecast_points,
            model_version="simple_v1"
        )
    
    def get_strategy_name(self) -> str:
        """Return name of the strategy (implements ForecastingStrategy)"""
        return "SimpleForecaster"
    
    def is_available(self) -> bool:
        """Check if strategy is available (implements ForecastingStrategy)"""
        return True  # Always available
    
    def get_history_size(self, camera_id: str) -> int:
        """Get number of historical observations for camera"""
        return len(self.history.get(camera_id, []))
    
    def clear_history(self, camera_id: str = None) -> None:
        """Clear history for specific camera or all cameras"""
        if camera_id:
            if camera_id in self.history:
                self.history[camera_id].clear()
                logger.info(f"Cleared history for {camera_id}")
        else:
            self.history.clear()
            logger.info("Cleared all history")
