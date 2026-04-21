"""KPI calculation engine — computes and persists KPI snapshots."""
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kpi.formulas import (
    calc_ai_quality_score,
    calc_department_kpi,
    calc_incident_score,
    calc_repeat_issue_score,
    calc_resolution_score,
    calc_work_completion_score,
)
from app.models.event import ParsedEvent
from app.models.kpi import KPISnapshot
from app.schemas.common import PeriodType
from app.core.logging import get_logger

logger = get_logger(__name__)


def _period_range(period_type: PeriodType, reference_date: date) -> tuple[date, date]:
    """Return (start, end) for the period containing reference_date."""
    if period_type == PeriodType.DAILY:
        return reference_date, reference_date
    if period_type == PeriodType.WEEKLY:
        start = reference_date - timedelta(days=reference_date.weekday())
        end = start + timedelta(days=6)
        return start, end
    # MONTHLY
    start = reference_date.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
    return start, end


async def _load_events(
    db: AsyncSession, start: date, end: date
) -> list[ParsedEvent]:
    result = await db.execute(
        select(ParsedEvent).where(
            and_(
                func.date(ParsedEvent.created_at) >= start,
                func.date(ParsedEvent.created_at) <= end,
            )
        )
    )
    return list(result.scalars().all())


async def calculate_kpi(
    db: AsyncSession,
    period_type: PeriodType,
    reference_date: Optional[date] = None,
) -> KPISnapshot:
    """
    Calculate KPI for the given period and upsert snapshot in DB.
    """
    ref = reference_date or datetime.utcnow().date()
    start, end = _period_range(period_type, ref)

    events = await _load_events(db, start, end)

    incidents = [e for e in events if e.record_type == "incident"]
    works = [e for e in events if e.record_type == "work"]
    risks = [e for e in events if e.record_type == "risk"]
    equipment = [e for e in events if e.record_type == "equipment"]
    notes = [e for e in events if e.record_type == "note"]

    critical_incidents = [e for e in incidents if e.severity == "critical"]
    resolved = [e for e in incidents if e.status == "resolved"]
    unresolved = [e for e in incidents if e.status not in ("resolved", "closed")]
    repeat = [e for e in incidents if e.repeat_issue]
    followups_open = [e for e in events if e.requires_followup and e.status not in ("resolved", "closed")]
    works_with_result = [w for w in works if w.result or w.actions_taken]

    # Resolution time
    resolution_times = [
        e.duration_minutes for e in resolved if e.duration_minutes and e.duration_minutes > 0
    ]
    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
    min_resolution = min(resolution_times) if resolution_times else None
    max_resolution = max(resolution_times) if resolution_times else None

    # AI scores
    ai_scores = [e.ai_score for e in events if e.ai_score is not None]
    ai_avg_score = sum(ai_scores) / len(ai_scores) if ai_scores else 50.0
    ai_confidences = [e.ai_confidence for e in events if e.ai_confidence is not None]
    ai_avg_confidence = sum(ai_confidences) / len(ai_confidences) if ai_confidences else None

    # KPI components
    inc_score = calc_incident_score(len(incidents), len(critical_incidents))
    res_score = calc_resolution_score(len(resolved), len(unresolved), avg_resolution)
    work_score = calc_work_completion_score(len(works), len(works_with_result))
    repeat_score = calc_repeat_issue_score(len(incidents), len(repeat))
    ai_qual_score = calc_ai_quality_score(ai_avg_score)
    dept_score = calc_department_kpi(inc_score, res_score, work_score, repeat_score, ai_qual_score)

    # Distributions
    severity_dist = dict(Counter(e.severity for e in incidents if e.severity))
    status_dist = dict(Counter(e.status for e in incidents if e.status))

    # Top channels / assets by incident count
    ch_counter = Counter(e.channel_id for e in incidents if e.channel_id)
    asset_counter = Counter(e.asset_id for e in incidents if e.asset_id)
    top_channels = [{"channel_id": k, "count": v} for k, v in ch_counter.most_common(5)]
    top_assets = [{"asset_id": k, "count": v} for k, v in asset_counter.most_common(5)]

    # Upsert snapshot
    result = await db.execute(
        select(KPISnapshot).where(
            and_(
                KPISnapshot.period_type == period_type.value,
                KPISnapshot.period_date == start,
            )
        )
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        snapshot = KPISnapshot(period_type=period_type.value, period_date=start)
        db.add(snapshot)

    snapshot.total_incidents = len(incidents)
    snapshot.critical_incidents = len(critical_incidents)
    snapshot.total_works = len(works)
    snapshot.total_risks = len(risks)
    snapshot.total_notes = len(notes)
    snapshot.total_equipment = len(equipment)
    snapshot.resolved_incidents = len(resolved)
    snapshot.unresolved_incidents = len(unresolved)
    snapshot.repeat_incidents = len(repeat)
    snapshot.followups_open = len(followups_open)
    snapshot.average_resolution_time_minutes = round(avg_resolution, 2) if avg_resolution else None
    snapshot.min_resolution_time_minutes = min_resolution
    snapshot.max_resolution_time_minutes = max_resolution
    snapshot.ai_average_score = round(ai_avg_score, 2)
    snapshot.ai_average_confidence = round(ai_avg_confidence, 3) if ai_avg_confidence else None
    snapshot.incident_score = inc_score
    snapshot.resolution_score = res_score
    snapshot.work_completion_score = work_score
    snapshot.repeat_issue_score = repeat_score
    snapshot.ai_quality_score = ai_qual_score
    snapshot.department_kpi_score = dept_score
    snapshot.top_channels = top_channels
    snapshot.top_assets = top_assets
    snapshot.severity_distribution = severity_dist
    snapshot.status_distribution = status_dist

    await db.flush()

    logger.info(
        "kpi_calculated",
        period_type=period_type.value,
        period_date=str(start),
        kpi_score=dept_score,
        total_incidents=len(incidents),
    )

    return snapshot


async def calculate_all_periods(
    db: AsyncSession,
    reference_date: Optional[date] = None,
) -> dict[str, KPISnapshot]:
    """Calculate and return KPI for daily, weekly, and monthly periods."""
    snapshots = {}
    for period_type in PeriodType:
        snapshot = await calculate_kpi(db, period_type, reference_date)
        snapshots[period_type.value] = snapshot
    return snapshots
