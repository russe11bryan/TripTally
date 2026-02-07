from __future__ import annotations

"""
SQLAlchemy adapter implementation for SavedListRepository.
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.saved_list import SavedList
from app.adapters.tables import SavedListTable


class SqlSavedListRepo:
    def __init__(self, db: Session):
        self.db = db

    def add(self, saved_list: SavedList) -> SavedList:
        """Create a new saved list."""
        row = SavedListTable(
            user_id=saved_list.user_id,
            name=saved_list.name,
            created_at=datetime.utcnow().isoformat() if not saved_list.created_at else saved_list.created_at.isoformat(),
            updated_at=datetime.utcnow().isoformat() if not saved_list.updated_at else saved_list.updated_at.isoformat(),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        
        return self._to_domain(row)

    def get_by_id(self, list_id: int) -> Optional[SavedList]:
        """Get a saved list by ID."""
        row = self.db.query(SavedListTable).filter(SavedListTable.id == list_id).first()
        return self._to_domain(row) if row else None

    def list_by_user(self, user_id: int) -> list[SavedList]:
        """Get all saved lists for a user."""
        rows = self.db.query(SavedListTable).filter(SavedListTable.user_id == user_id).all()
        return [self._to_domain(row) for row in rows]

    def update(self, saved_list: SavedList) -> SavedList:
        """Update an existing saved list."""
        row = self.db.query(SavedListTable).filter(SavedListTable.id == saved_list.id).first()
        if row:
            row.name = saved_list.name
            row.updated_at = datetime.utcnow().isoformat()
            self.db.commit()
            self.db.refresh(row)
        return self._to_domain(row) if row else saved_list

    def delete(self, list_id: int) -> bool:
        """Delete a saved list."""
        row = self.db.query(SavedListTable).filter(SavedListTable.id == list_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _to_domain(self, row: SavedListTable) -> SavedList:
        """Convert database row to domain model."""
        return SavedList(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            created_at=datetime.fromisoformat(row.created_at) if row.created_at else None,
            updated_at=datetime.fromisoformat(row.updated_at) if row.updated_at else None,
        )
