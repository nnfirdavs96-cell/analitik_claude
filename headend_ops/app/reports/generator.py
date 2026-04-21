"""Report generation orchestrator."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.provider_factory import get_fallback_provider, get_primary_provider
from app.core.config import settings
from app.core.exceptions import ReportGenerationError
from app.core.logging import get_logger
from app.kpi.engine import calculate_kpi
from app.models.event import ParsedEvent
from app.models.kpi import KPISnapshot
from app.models.report import Report, ReportItem
from app.reports.excel_exporter import generate_excel_report
from app.reports.pdf_exporter import generate_pdf_report
from app.schemas.common import PeriodType

logger = get_logger(__name__)


def _period_range(period_type: PeriodType, reference_date: date) -> tuple[date, date]:
    if period_type == PeriodType.DAILY:
        return reference_date, reference_date
    if period_type == PeriodType.WEEKLY:
        start = reference_date - timedelta(days=reference_date.weekday())
        return start, start + timedelta(days=6)
    start = reference_date.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
    return start, end


async def _load_events_for_report(
    db: AsyncSession, start: date, end: date
) -> list[ParsedEvent]:
    result = await db.execute(
        select(ParsedEvent)
        .options(selectinload(ParsedEvent.channel), selectinload(ParsedEvent.asset))
        .where(
            and_(
                func.date(ParsedEvent.created_at) >= start,
                func.date(ParsedEvent.created_at) <= end,
            )
        )
        .order_by(ParsedEvent.created_at.asc())
    )
    return list(result.scalars().all())


def _event_to_dict(event: ParsedEvent) -> dict:
    return {
        "id": event.id,
        "record_type": event.record_type,
        "title": event.title,
        "description": event.description,
        "event_datetime": event.event_datetime.isoformat() if event.event_datetime else None,
        "end_datetime": event.end_datetime.isoformat() if event.end_datetime else None,
        "duration_minutes": event.duration_minutes,
        "channel": event.channel.name if event.channel else event.channel_name_raw,
        "asset": event.asset.name if event.asset else event.asset_name_raw,
        "object_type": event.object_type,
        "severity": event.severity,
        "status": event.status,
        "root_cause": event.root_cause,
        "actions_taken": event.actions_taken,
        "result": event.result,
        "requires_followup": event.requires_followup,
        "followup_note": event.followup_note,
        "repeat_issue": event.repeat_issue,
        "recurrence_count": event.recurrence_count,
        "reporter_name": event.reporter_name,
        "tags": event.tags or [],
        "ai_confidence": event.ai_confidence,
        "ai_score": event.ai_score,
        "created_at": event.created_at.isoformat(),
    }


def _build_stats(events: list[ParsedEvent], kpi: Optional[KPISnapshot]) -> dict:
    incidents = [e for e in events if e.record_type == "incident"]
    works = [e for e in events if e.record_type == "work"]
    risks = [e for e in events if e.record_type == "risk"]
    equipment = [e for e in events if e.record_type == "equipment"]

    return {
        "total_events": len(events),
        "total_incidents": len(incidents),
        "total_works": len(works),
        "total_risks": len(risks),
        "total_equipment": len(equipment),
        "critical_incidents": len([e for e in incidents if e.severity == "critical"]),
        "resolved_incidents": len([e for e in incidents if e.status == "resolved"]),
        "unresolved_incidents": len([e for e in incidents if e.status not in ("resolved", "closed")]),
        "repeat_incidents": len([e for e in incidents if e.repeat_issue]),
        "followups_open": len([e for e in events if e.requires_followup]),
        "kpi_score": kpi.department_kpi_score if kpi else None,
        "avg_resolution_minutes": kpi.average_resolution_time_minutes if kpi else None,
    }


async def generate_report(
    db: AsyncSession,
    period_type: PeriodType,
    reference_date: Optional[date] = None,
    generate_excel: bool = True,
    generate_pdf: bool = True,
    generate_ai_summary: bool = True,
) -> Report:
    """Generate a complete management report for the given period."""
    ref = reference_date or datetime.now(timezone.utc).date()
    start, end = _period_range(period_type, ref)

    period_label_map = {
        PeriodType.DAILY: f"Ежедневный отчёт за {start.strftime('%d.%m.%Y')}",
        PeriodType.WEEKLY: f"Еженедельный отчёт {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}",
        PeriodType.MONTHLY: f"Ежемесячный отчёт за {start.strftime('%B %Y')}",
    }
    period_label = period_label_map[period_type]

    logger.info("report_generation_started", period_type=period_type.value, start=str(start))

    # Create report record
    report = Report(
        report_type=period_type.value,
        period_start=start,
        period_end=end,
        status="generating",
    )
    db.add(report)
    await db.flush()

    try:
        # Load data
        events = await _load_events_for_report(db, start, end)
        kpi = await calculate_kpi(db, period_type, ref)

        events_dicts = [_event_to_dict(e) for e in events]
        stats = _build_stats(events, kpi)

        # AI summary
        ai_summary_text = None
        if generate_ai_summary and events:
            try:
                provider = get_primary_provider()
                summary_result = await provider.generate_summary(
                    events_dicts, period_label
                )
                ai_summary_text = summary_result.summary_text
            except Exception as e:
                logger.warning("ai_summary_failed", error=str(e))
                fallback = get_fallback_provider()
                summary_result = await fallback.generate_summary(events_dicts, period_label)
                ai_summary_text = summary_result.summary_text

        # Build JSON data
        report_data = {
            "report_type": period_type.value,
            "period_label": period_label,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
            "kpi": {
                "department_kpi_score": kpi.department_kpi_score,
                "incident_score": kpi.incident_score,
                "resolution_score": kpi.resolution_score,
                "work_completion_score": kpi.work_completion_score,
                "repeat_issue_score": kpi.repeat_issue_score,
                "ai_quality_score": kpi.ai_quality_score,
                "severity_distribution": kpi.severity_distribution,
                "status_distribution": kpi.status_distribution,
                "top_channels": kpi.top_channels,
                "top_assets": kpi.top_assets,
            },
            "ai_summary": ai_summary_text,
            "events": {
                "incidents": [_event_to_dict(e) for e in events if e.record_type == "incident"],
                "works": [_event_to_dict(e) for e in events if e.record_type == "work"],
                "risks": [_event_to_dict(e) for e in events if e.record_type == "risk"],
                "equipment": [_event_to_dict(e) for e in events if e.record_type == "equipment"],
                "notes": [_event_to_dict(e) for e in events if e.record_type == "note"],
            },
        }

        # Paths
        reports_dir = settings.reports_path / period_type.value
        reports_dir.mkdir(parents=True, exist_ok=True)
        filename_base = f"report_{period_type.value}_{start.isoformat()}"

        # Save JSON
        json_path = reports_dir / f"{filename_base}.json"
        json_path.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Excel
        excel_path = None
        if generate_excel:
            excel_path = reports_dir / f"{filename_base}.xlsx"
            generate_excel_report(report_data, str(excel_path))

        # PDF
        pdf_path = None
        if generate_pdf:
            pdf_path = reports_dir / f"{filename_base}.pdf"
            generate_pdf_report(report_data, str(pdf_path))

        # Update report record
        report.status = "completed"
        report.json_path = str(json_path)
        report.excel_path = str(excel_path) if excel_path else None
        report.pdf_path = str(pdf_path) if pdf_path else None
        report.executive_summary = ai_summary_text
        report.kpi_data = report_data["kpi"]
        report.stats_data = stats

        # Link events
        for event in events:
            section = event.record_type + "s"
            db.add(ReportItem(report_id=report.id, event_id=event.id, section=section))

        await db.flush()
        logger.info("report_generated", report_id=report.id, events=len(events))
        return report

    except Exception as e:
        report.status = "failed"
        report.error_message = str(e)[:1000]
        await db.flush()
        logger.error("report_generation_failed", error=str(e), report_id=report.id)
        raise ReportGenerationError(f"Report generation failed: {e}") from e
