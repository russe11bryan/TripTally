"""
SQLAlchemy adapter implementation for MetricsRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.metrics import (
    Metrics, DrivingMetrics, PTMetrics, WalkingMetrics, CyclingMetrics
)
from app.adapters.tables import (
    MetricsTable, DrivingMetricsTable, PTMetricsTable,
    WalkingMetricsTable, CyclingMetricsTable
)
from app.ports.metrics_repo import MetricsRepository


class SqlMetricsRepo(MetricsRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, metrics: Metrics) -> Metrics:
        # route_id is database-only field, not in domain model
        # It should be set when metrics is linked to a route
        if isinstance(metrics, DrivingMetrics):
            row = DrivingMetricsTable(
                route_id=None,
                total_cost=metrics.total_cost,
                total_time_min=metrics.total_time_min,
                total_distance_km=metrics.total_distance_km,
                carbon_kg=metrics.carbon_kg,
                fuel_liters=metrics.fuel_liters
            )
        elif isinstance(metrics, PTMetrics):
            row = PTMetricsTable(
                route_id=None,
                total_cost=metrics.total_cost,
                total_time_min=metrics.total_time_min,
                total_distance_km=metrics.total_distance_km,
                carbon_kg=metrics.carbon_kg,
                fares=metrics.fares
            )
        elif isinstance(metrics, WalkingMetrics):
            row = WalkingMetricsTable(
                route_id=None,
                total_cost=metrics.total_cost,
                total_time_min=metrics.total_time_min,
                total_distance_km=metrics.total_distance_km,
                carbon_kg=metrics.carbon_kg,
                calories=metrics.calories
            )
        elif isinstance(metrics, CyclingMetrics):
            row = CyclingMetricsTable(
                route_id=None,
                total_cost=metrics.total_cost,
                total_time_min=metrics.total_time_min,
                total_distance_km=metrics.total_distance_km,
                carbon_kg=metrics.carbon_kg,
                calories=metrics.calories
            )
        else:
            row = MetricsTable(
                route_id=None,
                total_cost=metrics.total_cost,
                total_time_min=metrics.total_time_min,
                total_distance_km=metrics.total_distance_km,
                carbon_kg=metrics.carbon_kg
            )
        
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        metrics.id = row.id
        return metrics

    def get_by_id(self, metrics_id: int) -> Optional[Metrics]:
        row = self.db.query(MetricsTable).filter(MetricsTable.id == metrics_id).first()
        if not row:
            return None
        return self._map_to_domain(row)

    def get_by_route_id(self, route_id: int) -> Optional[Metrics]:
        row = self.db.query(MetricsTable).filter(MetricsTable.route_id == route_id).first()
        if not row:
            return None
        return self._map_to_domain(row)

    def list(self) -> list[Metrics]:
        rows = self.db.query(MetricsTable).all()
        return [self._map_to_domain(r) for r in rows]

    def update(self, metrics: Metrics) -> Metrics:
        row = self.db.query(MetricsTable).filter(MetricsTable.id == metrics.id).first()
        if row:
            # Don't update route_id - it's not in domain model
            row.total_cost = metrics.total_cost
            row.total_time_min = metrics.total_time_min
            row.total_distance_km = metrics.total_distance_km
            row.carbon_kg = metrics.carbon_kg
            
            if isinstance(metrics, DrivingMetrics) and isinstance(row, DrivingMetricsTable):
                row.fuel_liters = metrics.fuel_liters
            elif isinstance(metrics, PTMetrics) and isinstance(row, PTMetricsTable):
                row.fares = metrics.fares
            elif isinstance(metrics, WalkingMetrics) and isinstance(row, WalkingMetricsTable):
                row.calories = metrics.calories
            elif isinstance(metrics, CyclingMetrics) and isinstance(row, CyclingMetricsTable):
                row.calories = metrics.calories
            
            self.db.commit()
            self.db.refresh(row)
        return metrics

    def delete(self, metrics_id: int) -> bool:
        row = self.db.query(MetricsTable).filter(MetricsTable.id == metrics_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _map_to_domain(self, row: MetricsTable) -> Metrics:
        """Map database row to domain model based on type."""
        if row.type == "driving":
            return DrivingMetrics(
                id=row.id,
                total_cost=row.total_cost,
                total_time_min=row.total_time_min,
                total_distance_km=row.total_distance_km,
                carbon_kg=row.carbon_kg,
                fuel_liters=getattr(row, 'fuel_liters', 0.0)
            )
        elif row.type == "public_transport":
            return PTMetrics(
                id=row.id,
                total_cost=row.total_cost,
                total_time_min=row.total_time_min,
                total_distance_km=row.total_distance_km,
                carbon_kg=row.carbon_kg,
                fares=getattr(row, 'fares', 0.0)
            )
        elif row.type == "walking":
            return WalkingMetrics(
                id=row.id,
                total_cost=row.total_cost,
                total_time_min=row.total_time_min,
                total_distance_km=row.total_distance_km,
                carbon_kg=row.carbon_kg,
                calories=getattr(row, 'calories', 0.0)
            )
        elif row.type == "cycling":
            return CyclingMetrics(
                id=row.id,
                total_cost=row.total_cost,
                total_time_min=row.total_time_min,
                total_distance_km=row.total_distance_km,
                carbon_kg=row.carbon_kg,
                calories=getattr(row, 'calories', 0.0)
            )
        else:
            return Metrics(
                id=row.id,
                total_cost=row.total_cost,
                total_time_min=row.total_time_min,
                total_distance_km=row.total_distance_km,
                carbon_kg=row.carbon_kg
            )
