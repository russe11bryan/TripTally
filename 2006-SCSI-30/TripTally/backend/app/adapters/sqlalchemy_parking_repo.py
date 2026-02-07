"""
SQLAlchemy adapter implementations for Parking repositories.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.parking import Carpark, BikeSharingPoint
from app.adapters.tables import CarparkTable, BikeSharingPointTable
from app.ports.parking_repo import CarparkRepository, BikeSharingRepository


class SqlCarparkRepo(CarparkRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, carpark: Carpark) -> Carpark:
        row = CarparkTable(
            location_id=carpark.location_id,
            hourly_rate=carpark.hourly_rate,
            availability=carpark.availability
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        carpark.id = row.id
        return carpark

    def get_by_id(self, carpark_id: int) -> Optional[Carpark]:
        row = self.db.query(CarparkTable).filter(CarparkTable.id == carpark_id).first()
        if not row:
            return None
        return Carpark(
            id=row.id,
            location_id=row.location_id,
            hourly_rate=row.hourly_rate,
            availability=row.availability
        )

    def list(self) -> list[Carpark]:
        rows = self.db.query(CarparkTable).all()
        return [
            Carpark(
                id=r.id,
                location_id=r.location_id,
                hourly_rate=r.hourly_rate,
                availability=r.availability
            )
            for r in rows
        ]

    def list_by_location(self, location_id: int) -> list[Carpark]:
        rows = self.db.query(CarparkTable).filter(
            CarparkTable.location_id == location_id
        ).all()
        return [
            Carpark(
                id=r.id,
                location_id=r.location_id,
                hourly_rate=r.hourly_rate,
                availability=r.availability
            )
            for r in rows
        ]

    def update(self, carpark: Carpark) -> Carpark:
        row = self.db.query(CarparkTable).filter(CarparkTable.id == carpark.id).first()
        if row:
            row.location_id = carpark.location_id
            row.hourly_rate = carpark.hourly_rate
            row.availability = carpark.availability
            self.db.commit()
            self.db.refresh(row)
        return carpark

    def delete(self, carpark_id: int) -> bool:
        row = self.db.query(CarparkTable).filter(CarparkTable.id == carpark_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False


class SqlBikeSharingRepo(BikeSharingRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, point: BikeSharingPoint) -> BikeSharingPoint:
        row = BikeSharingPointTable(
            location_id=point.location_id,
            bikes_available=point.bikes_available
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        point.id = row.id
        return point

    def get_by_id(self, point_id: int) -> Optional[BikeSharingPoint]:
        row = self.db.query(BikeSharingPointTable).filter(
            BikeSharingPointTable.id == point_id
        ).first()
        if not row:
            return None
        return BikeSharingPoint(
            id=row.id,
            location_id=row.location_id,
            bikes_available=row.bikes_available
        )

    def list(self) -> list[BikeSharingPoint]:
        rows = self.db.query(BikeSharingPointTable).all()
        return [
            BikeSharingPoint(
                id=r.id,
                location_id=r.location_id,
                bikes_available=r.bikes_available
            )
            for r in rows
        ]

    def list_by_location(self, location_id: int) -> list[BikeSharingPoint]:
        rows = self.db.query(BikeSharingPointTable).filter(
            BikeSharingPointTable.location_id == location_id
        ).all()
        return [
            BikeSharingPoint(
                id=r.id,
                location_id=r.location_id,
                bikes_available=r.bikes_available
            )
            for r in rows
        ]

    def update(self, point: BikeSharingPoint) -> BikeSharingPoint:
        row = self.db.query(BikeSharingPointTable).filter(
            BikeSharingPointTable.id == point.id
        ).first()
        if row:
            row.location_id = point.location_id
            row.bikes_available = point.bikes_available
            self.db.commit()
            self.db.refresh(row)
        return point

    def delete(self, point_id: int) -> bool:
        row = self.db.query(BikeSharingPointTable).filter(
            BikeSharingPointTable.id == point_id
        ).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False
