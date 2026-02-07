"""
Domain models for Metrics
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Metrics:
    id: int
    total_cost: float = 0.0
    total_time_min: float = 0.0
    total_distance_km: float = 0.0
    carbon_kg: float = 0.0
    type: str = "metrics"


@dataclass
class DrivingMetrics(Metrics):
    fuel_usage_per_km: float = 0.0
    fuel_cost_per_liter: float = 0.0
    fuel_liters: float = 0.0
    type: str = "driving"


@dataclass
class PTMetrics(Metrics):
    busFares: float = 0.0
    mrtFares: float = 0.0 
    fares: float = 0.0
    type: str = "public_transport"


@dataclass
class WalkingMetrics(Metrics):
    calories: float = 0.0
    type: str = "walking"


@dataclass
class CyclingMetrics(Metrics):
    calories: float = 0.0
    type: str = "cycling"
