"""Schemas for report generation."""
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.common import PeriodType


class ReportRequest(BaseModel):
    report_type: PeriodType
    period_start: date
    period_end: Optional[date] = None  # auto-calculated if not provided
    generate_excel: bool = True
    generate_pdf: bool = True
    generate_ai_summary: bool = True


class ReportRead(BaseModel):
    id: int
    report_type: str
    period_start: date
    period_end: date
    status: str
    json_path: Optional[str] = None
    excel_path: Optional[str] = None
    pdf_path: Optional[str] = None
    executive_summary: Optional[str] = None
    ai_generated_summary: Optional[str] = None
    kpi_data: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueItem(BaseModel):
    id: int
    event_id: int
    reason: str
    original_json: Optional[dict] = None
    corrected_json: Optional[dict] = None
    status: str
    resolved_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewCorrection(BaseModel):
    corrected_json: dict
    resolved_by: str
    notes: Optional[str] = None
