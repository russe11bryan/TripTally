# Pydantic request/response models for report
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReportCreate(BaseModel):
    """Base schema for creating a report."""
    user_id: int = Field(..., description="ID of user creating the report")
    type: str = Field(..., description="Report type: incident, technical")


class IncidentReportCreate(ReportCreate):
    """Schema for creating an incident report."""
    start_location_id: int = Field(..., description="Starting location of incident")
    end_location_id: int = Field(..., description="Ending location of incident")
    obstruction_type: str = Field(..., description="Type of obstruction: roadblock, accident, construction, etc.")
    description: str = Field(..., description="Detailed description of the incident")
    type: str = Field(default="incident", description="Always 'incident' for this type")


class TechnicalReportCreate(ReportCreate):
    """Schema for creating a technical report."""
    description: str = Field(..., description="Detailed description of the technical issue")
    type: str = Field(default="technical", description="Always 'technical' for this type")


class ReportUpdate(BaseModel):
    """Schema for updating a report."""
    status: Optional[str] = Field(None, description="Report status: open, in_progress, resolved, closed")
    resolved: Optional[bool] = Field(None, description="Whether incident is resolved (incident reports only)")


class ReportOut(BaseModel):
    """Schema for report response."""
    id: int
    user_id: Optional[int]
    time: Optional[datetime]
    status: str
    type: str

    class Config:
        from_attributes = True


class IncidentReportOut(ReportOut):
    """Schema for incident report response."""
    start_location_id: Optional[int]
    end_location_id: Optional[int]
    obstruction_type: str
    description: str
    resolved: bool
    type: str = "incident"

    class Config:
        from_attributes = True


class TechnicalReportOut(ReportOut):
    """Schema for technical report response."""
    description: str
    type: str = "technical"

    class Config:
        from_attributes = True

