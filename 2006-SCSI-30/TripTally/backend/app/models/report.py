"""
Domain models for Reports
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Report:
    id: int
    user_id: Optional[int] = None
    time: Optional[datetime] = None
    status: str = "open"
    type: str = "report"
    # TODO: Add links to images


@dataclass
class IncidentReport(Report):
    start_location_id: Optional[int] = None
    end_location_id: Optional[int] = None
    obstruction_type: str = ""
    description: str = ""
    resolved: bool = False
    type: str = "incident"


@dataclass
class TechnicalReport(Report):
    description: str = ""
    category: str = ""
    added_by: Optional[str] = None  # Changed to store username instead of user_id
    type: str = "technical"
