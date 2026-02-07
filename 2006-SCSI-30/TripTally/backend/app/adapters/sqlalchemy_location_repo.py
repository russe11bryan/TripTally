from __future__ import annotations

"""
SQLAlchemy adapter implementation for LocationRepository.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.location import Location
from app.adapters.tables import LocationTable
from app.ports.location_repo import LocationRepository


class SqlLocationRepo(LocationRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, location: Location) -> Location:
        row = LocationTable(
            name=location.name,
            lat=location.lat,
            lng=location.lng
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        location.id = row.id
        return location

    def get_by_id(self, location_id: int) -> Optional[Location]:
        row = self.db.query(LocationTable).filter(LocationTable.id == location_id).first()
        if not row:
            return None
        return Location(id=row.id, name=row.name, lat=row.lat, lng=row.lng)

    def list(self) -> list[Location]:
        rows = self.db.query(LocationTable).all()
        return [Location(id=r.id, name=r.name, lat=r.lat, lng=r.lng) for r in rows]

    def update(self, location: Location) -> Location:
        row = self.db.query(LocationTable).filter(LocationTable.id == location.id).first()
        if row:
            row.name = location.name
            row.lat = location.lat
            row.lng = location.lng
            self.db.commit()
            self.db.refresh(row)
        return location

    def delete(self, location_id: int) -> bool:
        row = self.db.query(LocationTable).filter(LocationTable.id == location_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False
