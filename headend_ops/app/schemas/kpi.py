"""KPI schemas."""
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.common import PeriodType


class KPISnapshotRead(BaseModel):
    id: int
    period_type: PeriodType
    period_date: date
    total_incidents: int
    critical_incidents: int
    total_works: int
    total_risks: int
    total_notes: int
    total_equipment: int
    resolved_incidents: int
    unresolved_incidents: int
    repeat_incidents: int
    followups_open: int
    average_resolution_time_minutes: Optional[float] = None
    ai_average_score: Optional[float] = None
    incident_score: Optional[float] = None
    resolution_score: Optional[float] = None
    work_completion_score: Optional[float] = None
    repeat_issue_score: Optional[float] = None
    ai_quality_score: Optional[float] = None
    department_kpi_score: Optional[float] = None
    top_channels: Optional[List[dict]] = None
    top_assets: Optional[List[dict]] = None
    severity_distribution: Optional[Dict[str, int]] = None
    status_distribution: Optional[Dict[str, int]] = None
    created_at: str

    model_config = {"from_attributes": True}


class KPIDashboard(BaseModel):
    """Dashboard-ready KPI aggregation."""
    period_type: PeriodType
    period_date: date
    department_kpi_score: float
    total_incidents: int
    critical_incidents: int
    total_works: int
    resolved_incidents: int
    unresolved_incidents: int
    repeat_incidents: int
    average_resolution_time_minutes: Optional[float]
    followups_open: int
    top_channels: List[dict]
    top_assets: List[dict]
    severity_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    kpi_trend: List[dict]  # last N periods for trend chart
