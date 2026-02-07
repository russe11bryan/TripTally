"""
SQLAlchemy adapter implementation for ReportRepository.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.models.report import Report, TechnicalReport
from app.adapters.tables import ReportTable, TechnicalReportTable
from app.ports.report_repo import ReportRepository


class SqlReportRepo(ReportRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, report: Report) -> Report:
        if isinstance(report, TechnicalReport):
            row = TechnicalReportTable(
                user_id=report.user_id,
                description=report.description,
                category=report.category,
                added_by=report.added_by
            )
        else:
            row = ReportTable(user_id=report.user_id)
        
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        report.id = row.id
        return report

    def get_by_id(self, report_id: int) -> Optional[Report]:
        row = self.db.query(ReportTable).filter(ReportTable.id == report_id).first()
        if not row:
            return None
        return self._map_to_domain(row)

    def list(self) -> list[Report]:
        rows = self.db.query(ReportTable).all()
        return [self._map_to_domain(r) for r in rows]

    def list_by_user(self, user_id: int) -> list[Report]:
        rows = self.db.query(ReportTable).filter(ReportTable.user_id == user_id).all()
        return [self._map_to_domain(r) for r in rows]

    def update(self, report: Report) -> Report:
        row = self.db.query(ReportTable).filter(ReportTable.id == report.id).first()
        if row:
            if isinstance(report, TechnicalReport) and isinstance(row, TechnicalReportTable):
                row.description = report.description
                row.category = report.category
                row.added_by = report.added_by
            self.db.commit()
            self.db.refresh(row)
        return report

    def delete(self, report_id: int) -> bool:
        row = self.db.query(ReportTable).filter(ReportTable.id == report_id).first()
        if row:
            self.db.delete(row)
            self.db.commit()
            return True
        return False

    def _map_to_domain(self, row: ReportTable) -> Report:
        """Map database row to domain model based on type."""
        if row.type == "technical":
            return TechnicalReport(
                id=row.id,
                user_id=row.user_id,
                description=getattr(row, 'description', ''),
                category=getattr(row, 'category', ''),
                added_by=getattr(row, 'added_by', None)
            )
        else:
            return Report(id=row.id, user_id=row.user_id)
