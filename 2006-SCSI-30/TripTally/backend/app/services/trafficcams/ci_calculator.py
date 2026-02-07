"""
CI Calculator Service
Business logic for Congestion Index calculation
"""

import math
from datetime import datetime
from typing import Tuple

from .config import CIConfig
from .models import DetectionResult
from .logger import get_logger

logger = get_logger("ci_calculator")


class CICalculator:
    """Calculate Congestion Index from detection results"""
    
    # Vehicle class weights (COCO IDs)
    CLASS_WEIGHTS = {
        1: 0.5,   # bicycle
        2: 1.0,   # car
        3: 1.0,   # motorcycle
        5: 2.0,   # bus
        7: 2.0,   # truck
    }
    
    def __init__(self, config: CIConfig):
        self.config = config
    
    def calculate_weighted_count(self, detection: DetectionResult) -> float:
        """Calculate weighted vehicle count"""
        weighted = 0.0
        for class_id in detection.class_ids:
            weight = self.CLASS_WEIGHTS.get(int(class_id), 1.0)
            weighted += weight
        return weighted
    
    def calculate_area_ratio(self, detection: DetectionResult, img_area: float) -> float:
        """Calculate ratio of area covered by vehicles"""
        total_area = 0.0
        for box in detection.boxes:
            x1, y1, x2, y2 = box
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            total_area += width * height
        
        return total_area / max(1.0, img_area)
    
    def calculate_ci(self, weighted_count: float, area_ratio: float, motion: float) -> float:
        """
        Calculate Congestion Index
        
        Args:
            weighted_count: Weighted vehicle count
            area_ratio: Ratio of image covered by vehicles
            motion: Motion score from frame differencing
            
        Returns:
            CI value between 0 and 1
        """
        # Normalize components
        veh_density = self._clip(weighted_count / self.config.k_count)
        area_density = self._clip(area_ratio / self.config.k_area)
        
        # Raw CI from density measures
        ci_raw = (self.config.w_dens * veh_density + 
                  self.config.w_area * area_density)
        
        # Motion relief factor (high motion = flowing traffic = lower congestion)
        motion_relief = 1.0 - self._clip(motion / self.config.k_motion)
        
        # Final CI
        ci = self._clip(
            self.config.w_ciraw * ci_raw + 
            self.config.w_mrel * motion_relief
        )
        
        return ci
    
    def calculate_temporal_features(self, timestamp: datetime) -> Tuple[int, int, int, bool, float, float]:
        """
        Extract temporal features
        
        Returns:
            (minute_of_day, hour, day_of_week, is_weekend, sin_t_h, cos_t_h)
        """
        minute_of_day = timestamp.hour * 60 + timestamp.minute
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        is_weekend = day_of_week >= 5
        
        # Cyclical encoding of time
        t_h = timestamp.hour + timestamp.minute / 60.0
        sin_t_h = math.sin(2 * math.pi * t_h / 24.0)
        cos_t_h = math.cos(2 * math.pi * t_h / 24.0)
        
        return minute_of_day, hour, day_of_week, is_weekend, sin_t_h, cos_t_h
    
    @staticmethod
    def _clip(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clip value to range"""
        return max(min_val, min(max_val, value))
