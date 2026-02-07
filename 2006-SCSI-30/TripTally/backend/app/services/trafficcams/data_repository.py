"""
Data Repository Pattern
Defines interface for different data storage implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from .models import Camera, CIState, CIForecast


class DataRepository(ABC):
    """Abstract base class for data repository implementations"""
    
    @abstractmethod
    def save_ci_state(self, state: CIState) -> bool:
        """
        Save current CI state
        
        Args:
            state: CI state to save
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_ci_state(self, camera_id: str) -> Optional[CIState]:
        """
        Retrieve current CI state for camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            CIState or None if not found
        """
        pass
    
    @abstractmethod
    def save_forecast(self, forecast: CIForecast) -> bool:
        """
        Save forecast
        
        Args:
            forecast: Forecast to save
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_forecast(self, camera_id: str) -> Optional[CIForecast]:
        """
        Retrieve forecast for camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            CIForecast or None if not found
        """
        pass
    
    @abstractmethod
    def save_camera_metadata(self, camera: Camera) -> bool:
        """
        Save camera metadata
        
        Args:
            camera: Camera object
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_camera_metadata(self, camera_id: str) -> Optional[Camera]:
        """
        Retrieve camera metadata
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Camera or None if not found
        """
        pass
    
    @abstractmethod
    def list_cameras(self) -> List[str]:
        """
        List all camera IDs
        
        Returns:
            List of camera IDs
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if repository is healthy
        
        Returns:
            True if healthy
        """
        pass
    
    @abstractmethod
    def get_repository_name(self) -> str:
        """Return name of the repository implementation"""
        pass
