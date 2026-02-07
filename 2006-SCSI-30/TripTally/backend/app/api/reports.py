from __future__ import annotations

"""
Report API endpoints for incident and technical reports.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.db import get_db
from app.adapters.sqlalchemy_report_repo import SqlReportRepo
from app.models.report import Report, IncidentReport, TechnicalReport

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============= Pydantic Schemas =============
class TechnicalReportCreate(BaseModel):
    category: str
    description: str
    user_id: Optional[int] = None
    added_by: Optional[str] = None  # Changed to string for username


class IncidentReportCreate(BaseModel):
    start_location_id: Optional[int] = None
    end_location_id: Optional[int] = None
    obstruction_type: str
    description: str
    user_id: Optional[int] = None


class TechnicalReportResponse(BaseModel):
    id: int
    user_id: Optional[int]
    category: str
    description: str
    added_by: Optional[str]  # Changed to string for username
    type: str

    class Config:
        from_attributes = True


class IncidentReportResponse(BaseModel):
    id: int
    user_id: Optional[int]
    start_location_id: Optional[int]
    end_location_id: Optional[int]
    obstruction_type: str
    description: str
    resolved: bool
    type: str

    class Config:
        from_attributes = True


# ============= API Endpoints =============
@router.post("/technical", response_model=TechnicalReportResponse, status_code=201)
def create_technical_report(payload: TechnicalReportCreate, db: Session = Depends(get_db)):
    """Create a new technical report."""
    repo = SqlReportRepo(db)
    report = TechnicalReport(
        id=0,
        user_id=payload.user_id,
        category=payload.category,
        description=payload.description,
        added_by=payload.added_by
    )
    created_report = repo.add(report)
    return created_report


@router.post("/incident", response_model=IncidentReportResponse, status_code=201)
def create_incident_report(payload: IncidentReportCreate, db: Session = Depends(get_db)):
    """Create a new incident report."""
    repo = SqlReportRepo(db)
    report = IncidentReport(
        id=0,
        user_id=payload.user_id,
        start_location_id=payload.start_location_id,
        end_location_id=payload.end_location_id,
        obstruction_type=payload.obstruction_type,
        description=payload.description,
        resolved=False
    )
    created_report = repo.add(report)
    return created_report


@router.get("/technical", response_model=list[TechnicalReportResponse])
def list_technical_reports(db: Session = Depends(get_db)):
    """Get all technical reports."""
    repo = SqlReportRepo(db)
    all_reports = repo.list()
    # Filter only technical reports
    technical_reports = [r for r in all_reports if isinstance(r, TechnicalReport)]
    return technical_reports


@router.get("/incident", response_model=list[IncidentReportResponse])
def list_incident_reports(db: Session = Depends(get_db)):
    """Get all incident reports."""
    repo = SqlReportRepo(db)
    return repo.list_incident_reports()


@router.get("/{report_id}", response_model=TechnicalReportResponse | IncidentReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a report by ID."""
    repo = SqlReportRepo(db)
    report = repo.get_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report."""
    repo = SqlReportRepo(db)
    success = repo.delete(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return None
