from __future__ import annotations

"""
SQLAlchemy adapter implementation for SavedPlaceRepository.
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.saved_place import SavedPlace
from app.adapters.tables import SavedPlaceTable


class SqlSavedPlaceRepo:
    def __init__(self, db: Session):
        self.db = db

    def add(self, saved_place: SavedPlace) -> SavedPlace:
        """Add a new place to a saved list."""
        row = SavedPlaceTable(
            list_id=saved_place.list_id,
            name=saved_place.name,
            address=saved_place.address,
            latitude=saved_place.latitude,
            longitude=saved_place.longitude,
            created_at=datetime.utcnow().isoformat() if not saved_place.created_at else saved_place.created_at.isoformat(),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        
        return self._to_domain(row)

    def get_by_id(self, place_id: int) -> Optional[SavedPlace]:
        """Get a saved place by ID."""
        row = self.db.query(SavedPlaceTable).filter(SavedPlaceTable.id == place_id).first()
        return self._to_domain(row) if row else None

    def list_by_list_id(self, list_id: int) -> list[SavedPlace]:
        """Get all places in a saved list."""
        rows = self.db.query(SavedPlaceTable).filter(SavedPlaceTable.list_id == list_id).all()
        return [self._to_domain(row) for row in rows]

    def update(self, saved_place: SavedPlace) -> SavedPlace:
        """Update an existing saved place."""
        row = self.db.query(SavedPlaceTable).filter(SavedPlaceTable.id == saved_place.id).first()
        if row:
            row.name = saved_place.name
            row.address = saved_place.address
            row.latitude = saved_place.latitude
            row.longitude = saved_place.longitude
            self.db.commit()
            self.db.refresh(row)
        return self._to_domain(row) if row else saved_place

    def delete(self, place_id: int) -> bool:
        """Delete a saved place."""
        row = self.db.query(SavedPlaceTable).filter(SavedPlaceTable.id == place_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: SavedPlaceTable) -> SavedPlace:
        """Convert database row to domain model."""
        return SavedPlace(
            id=row.id,
            list_id=row.list_id,
            name=row.name,
            address=row.address,
            latitude=row.latitude,
            longitude=row.longitude,
            created_at=datetime.fromisoformat(row.created_at) if row.created_at else None,
        )
