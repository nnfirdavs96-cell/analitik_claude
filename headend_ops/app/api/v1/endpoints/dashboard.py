"""Dashboard aggregation endpoints — dashboard-ready data."""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.kpi.engine import calculate_kpi
from app.models.event import ParsedEvent
from app.models.kpi import KPISnapshot
from app.schemas.common import PeriodType

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Dashboard summary — all KPIs and stats")
async def dashboard_summary(
    reference_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Returns all dashboard-relevant data in one call."""
    ref = reference_date or datetime.utcnow().date()

    monthly_kpi = await calculate_kpi(db, PeriodType.MONTHLY, ref)
    weekly_kpi = await calculate_kpi(db, PeriodType.WEEKLY, ref)
    daily_kpi = await calculate_kpi(db, PeriodType.DAILY, ref)

    # Trend: last 6 months
    trend_result = await db.execute(
        select(KPISnapshot)
        .where(KPISnapshot.period_type == "monthly")
        .order_by(KPISnapshot.period_date.desc())
        .limit(6)
    )
    trend = [
        {
            "period": str(s.period_date),
            "kpi_score": s.department_kpi_score,
            "incidents": s.total_incidents,
            "resolved": s.resolved_incidents,
        }
        for s in reversed(trend_result.scalars().all())
    ]

    # Recent unresolved incidents
    unresolved_result = await db.execute(
        select(ParsedEvent)
        .where(
            and_(
                ParsedEvent.record_type == "incident",
                ParsedEvent.status.not_in(["resolved", "closed"]),
            )
        )
        .order_by(ParsedEvent.created_at.desc())
        .limit(10)
    )
    unresolved = [
        {
            "id": e.id,
            "title": e.title,
            "severity": e.severity,
            "created_at": e.created_at.isoformat(),
        }
        for e in unresolved_result.scalars().all()
    ]

    return {
        "labels": {
            "kpi_score": "KPI отдела",
            "total_incidents": "Всего инцидентов",
            "critical_incidents": "Критических",
            "resolved": "Устранено",
            "unresolved": "Не устранено",
            "repeat": "Повторных",
            "works": "Работ",
            "risks": "Рисков",
            "avg_resolution": "Среднее время устранения (мин)",
        },
        "monthly": {
            "kpi_score": monthly_kpi.department_kpi_score,
            "total_incidents": monthly_kpi.total_incidents,
            "critical_incidents": monthly_kpi.critical_incidents,
            "resolved_incidents": monthly_kpi.resolved_incidents,
            "unresolved_incidents": monthly_kpi.unresolved_incidents,
            "repeat_incidents": monthly_kpi.repeat_incidents,
            "total_works": monthly_kpi.total_works,
            "total_risks": monthly_kpi.total_risks,
            "average_resolution_time_minutes": monthly_kpi.average_resolution_time_minutes,
            "followups_open": monthly_kpi.followups_open,
            "top_channels": monthly_kpi.top_channels or [],
            "top_assets": monthly_kpi.top_assets or [],
            "severity_distribution": monthly_kpi.severity_distribution or {},
            "status_distribution": monthly_kpi.status_distribution or {},
        },
        "weekly": {
            "kpi_score": weekly_kpi.department_kpi_score,
            "total_incidents": weekly_kpi.total_incidents,
        },
        "daily": {
            "kpi_score": daily_kpi.department_kpi_score,
            "total_incidents": daily_kpi.total_incidents,
        },
        "trend": trend,
        "unresolved_incidents": unresolved,
    }
