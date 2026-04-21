"""Report and audit models."""
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    """Generated management report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily | weekly | monthly
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | generating | completed | failed

    # Paths to generated files
    json_path: Mapped[Optional[str]] = mapped_column(String(500))
    excel_path: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Summary narrative in Russian
    executive_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_generated_summary: Mapped[Optional[str]] = mapped_column(Text)

    # Snapshot of KPI data at report generation time
    kpi_data: Mapped[Optional[dict]] = mapped_column(JSON)
    stats_data: Mapped[Optional[dict]] = mapped_column(JSON)

    error_message: Mapped[Optional[str]] = mapped_column(Text)

    items: Mapped[list["ReportItem"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class ReportItem(Base):
    """Individual event reference included in a report."""

    __tablename__ = "report_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id", ondelete="CASCADE"))
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("parsed_events.id"))
    section: Mapped[Optional[str]] = mapped_column(String(100))  # incidents, works, risks, etc.

    report: Mapped["Report"] = relationship(back_populates="items")


class AuditLog(Base, TimestampMixin):
    """Audit trail for all significant actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    actor: Mapped[Optional[str]] = mapped_column(String(200))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))


class AppSetting(Base, TimestampMixin):
    """Key-value application settings stored in DB."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Integer, default=False)
