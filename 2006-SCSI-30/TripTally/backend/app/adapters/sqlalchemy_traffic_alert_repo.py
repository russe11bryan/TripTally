"""
SQLAlchemy adapter implementation for TrafficAlertRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.traffic_alert import TrafficAlert
from app.adapters.tables import TrafficAlertTable
from app.ports.traffic_alert_repo import TrafficAlertRepository


class SqlTrafficAlertRepo(TrafficAlertRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, alert: TrafficAlert) -> TrafficAlert:
        """Add a new traffic alert to the database."""
        row = TrafficAlertTable(
            alert_id=alert.alert_id,
            obstruction_type=alert.obstruction_type,
            latitude=alert.latitude,
            longitude=alert.longitude,
            location_name=alert.location_name,
            reported_by=alert.reported_by,
            delay_duration=alert.delay_duration,
            status=alert.status,
            created_at=alert.created_at.isoformat() if alert.created_at else None,
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        alert.id = row.id
        return alert

    def get_by_id(self, alert_id: int) -> Optional[TrafficAlert]:
        """Get traffic alert by database ID."""
        row = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.id == alert_id
        ).first()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_alert_id(self, alert_id: str) -> Optional[TrafficAlert]:
        """Get traffic alert by external alert ID."""
        row = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.alert_id == alert_id
        ).first()
        if not row:
            return None
        return self._to_domain(row)

    def list(self) -> list[TrafficAlert]:
        """List all traffic alerts."""
        rows = self.db.query(TrafficAlertTable).all()
        return [self._to_domain(r) for r in rows]

    def list_active(self) -> list[TrafficAlert]:
        """List all active traffic alerts."""
        rows = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.status == "active"
        ).all()
        return [self._to_domain(r) for r in rows]

    def list_by_status(self, status: str) -> list[TrafficAlert]:
        """List traffic alerts by status."""
        rows = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.status == status
        ).all()
        return [self._to_domain(r) for r in rows]

    def update(self, alert: TrafficAlert) -> TrafficAlert:
        """Update an existing traffic alert."""
        row = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.id == alert.id
        ).first()
        if row:
            row.alert_id = alert.alert_id
            row.obstruction_type = alert.obstruction_type
            row.latitude = alert.latitude
            row.longitude = alert.longitude
            row.location_name = alert.location_name
            row.reported_by = alert.reported_by
            row.delay_duration = alert.delay_duration
            row.status = alert.status
            row.created_at = alert.created_at.isoformat() if alert.created_at else None
            row.resolved_at = alert.resolved_at.isoformat() if alert.resolved_at else None
            self.db.commit()
            self.db.refresh(row)
        return alert

    def delete(self, alert_id: int) -> bool:
        """Delete a traffic alert."""
        row = self.db.query(TrafficAlertTable).filter(
            TrafficAlertTable.id == alert_id
        ).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: TrafficAlertTable) -> TrafficAlert:
        """Convert database row to domain model."""
        from datetime import datetime
        
        return TrafficAlert(
            id=row.id,
            alert_id=row.alert_id,
            obstruction_type=row.obstruction_type,
            latitude=row.latitude,
            longitude=row.longitude,
            location_name=row.location_name,
            reported_by=row.reported_by,
            delay_duration=row.delay_duration,
            status=row.status,
            created_at=datetime.fromisoformat(row.created_at) if row.created_at else None,
            resolved_at=datetime.fromisoformat(row.resolved_at) if row.resolved_at else None,
        )
