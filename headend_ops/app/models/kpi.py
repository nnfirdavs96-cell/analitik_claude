"""KPI snapshot models."""
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class KPISnapshot(Base, TimestampMixin):
    """
    Pre-calculated KPI metrics for a given period.
    Recalculated each time a new event is ingested.
    """

    __tablename__ = "kpi_snapshots"
    __table_args__ = (
        UniqueConstraint("period_type", "period_date", name="uq_kpi_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily | weekly | monthly
    period_date: Mapped[date] = mapped_column(Date, nullable=False)  # start date of period

    # Raw counts
    total_incidents: Mapped[int] = mapped_column(Integer, default=0)
    critical_incidents: Mapped[int] = mapped_column(Integer, default=0)
    total_works: Mapped[int] = mapped_column(Integer, default=0)
    total_risks: Mapped[int] = mapped_column(Integer, default=0)
    total_notes: Mapped[int] = mapped_column(Integer, default=0)
    total_equipment: Mapped[int] = mapped_column(Integer, default=0)
    resolved_incidents: Mapped[int] = mapped_column(Integer, default=0)
    unresolved_incidents: Mapped[int] = mapped_column(Integer, default=0)
    repeat_incidents: Mapped[int] = mapped_column(Integer, default=0)
    followups_open: Mapped[int] = mapped_column(Integer, default=0)

    # Time metrics
    average_resolution_time_minutes: Mapped[Optional[float]] = mapped_column(Float)
    min_resolution_time_minutes: Mapped[Optional[float]] = mapped_column(Float)
    max_resolution_time_minutes: Mapped[Optional[float]] = mapped_column(Float)

    # Quality metrics
    ai_average_score: Mapped[Optional[float]] = mapped_column(Float)
    ai_average_confidence: Mapped[Optional[float]] = mapped_column(Float)

    # KPI component scores (0-100)
    incident_score: Mapped[Optional[float]] = mapped_column(Float)
    resolution_score: Mapped[Optional[float]] = mapped_column(Float)
    work_completion_score: Mapped[Optional[float]] = mapped_column(Float)
    repeat_issue_score: Mapped[Optional[float]] = mapped_column(Float)
    ai_quality_score: Mapped[Optional[float]] = mapped_column(Float)

    # Final weighted KPI score (0-100)
    department_kpi_score: Mapped[Optional[float]] = mapped_column(Float)

    # Top lists stored as JSON
    top_channels: Mapped[Optional[list]] = mapped_column(JSON)
    top_assets: Mapped[Optional[list]] = mapped_column(JSON)
    top_root_causes: Mapped[Optional[list]] = mapped_column(JSON)
    severity_distribution: Mapped[Optional[dict]] = mapped_column(JSON)
    status_distribution: Mapped[Optional[dict]] = mapped_column(JSON)
