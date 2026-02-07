"""
Forecasting Strategy Pattern
Defines interface for different forecasting strategies
"""

from abc import ABC, abstractmethod
from typing import List
from .models import CIState, CIForecast


class ForecastingStrategy(ABC):
    """Abstract base class for forecasting strategies"""
    
    @abstractmethod
    def generate_forecast(self, state: CIState) -> CIForecast:
        """
        Generate forecast for given CI state
        
        Args:
            state: Current CI state
            
        Returns:
            CIForecast with predictions
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return name of the strategy"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if strategy is available (e.g., ML models loaded)"""
        pass
