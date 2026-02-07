"""
SQLAlchemy adapter implementation for SuggestionRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.suggestion import Suggestion
from app.adapters.tables import SuggestionTable
from app.ports.suggestion_repo import SuggestionRepository


class SqlSuggestionRepo(SuggestionRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, suggestion: Suggestion) -> Suggestion:
        row = SuggestionTable(
            title=suggestion.title,
            category=suggestion.category,
            description=suggestion.description,
            added_by=suggestion.added_by,
            created_at=datetime.now().isoformat() if not suggestion.created_at else suggestion.created_at.isoformat(),
            status=suggestion.status,
            likes=suggestion.likes,
            latitude=suggestion.latitude,
            longitude=suggestion.longitude,
            location_name=suggestion.location_name
        )
        
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        suggestion.id = row.id
        return suggestion

    def get_by_id(self, suggestion_id: int) -> Optional[Suggestion]:
        row = self.db.query(SuggestionTable).filter(SuggestionTable.id == suggestion_id).first()
        if not row:
            return None
        return self._map_to_domain(row)

    def list(self) -> list[Suggestion]:
        rows = self.db.query(SuggestionTable).order_by(SuggestionTable.created_at.desc()).all()
        return [self._map_to_domain(r) for r in rows]

    def list_by_status(self, status: str) -> list[Suggestion]:
        rows = self.db.query(SuggestionTable).filter(SuggestionTable.status == status).order_by(SuggestionTable.created_at.desc()).all()
        return [self._map_to_domain(r) for r in rows]

    def update(self, suggestion: Suggestion) -> Suggestion:
        row = self.db.query(SuggestionTable).filter(SuggestionTable.id == suggestion.id).first()
        if row:
            row.title = suggestion.title
            row.category = suggestion.category
            row.description = suggestion.description
            row.added_by = suggestion.added_by
            row.status = suggestion.status
            row.likes = suggestion.likes
            row.latitude = suggestion.latitude
            row.longitude = suggestion.longitude
            row.location_name = suggestion.location_name
            self.db.commit()
            self.db.refresh(row)
        return suggestion

    def delete(self, suggestion_id: int) -> bool:
        row = self.db.query(SuggestionTable).filter(SuggestionTable.id == suggestion_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _map_to_domain(self, row: SuggestionTable) -> Suggestion:
        """Map database row to domain model."""
        created_at = None
        if row.created_at:
            try:
                created_at = datetime.fromisoformat(row.created_at)
            except (ValueError, TypeError):
                pass
        
        return Suggestion(
            id=row.id,
            title=row.title,
            category=row.category,
            description=row.description,
            added_by=row.added_by,
            created_at=created_at,
            status=row.status,
            likes=row.likes,
            latitude=row.latitude,
            longitude=row.longitude,
            location_name=row.location_name
        )
