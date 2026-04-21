"""KPI endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.kpi.engine import calculate_all_periods, calculate_kpi
from app.models.kpi import KPISnapshot
from app.schemas.common import PeriodType
from app.schemas.kpi import KPISnapshotRead

router = APIRouter(prefix="/kpi", tags=["KPI"])


@router.post("/calculate", response_model=dict, summary="Trigger KPI recalculation")
async def trigger_kpi_calculation(
    reference_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Recalculate KPI for all periods (daily, weekly, monthly)."""
    snapshots = await calculate_all_periods(db, reference_date)
    return {
        k: {
            "department_kpi_score": s.department_kpi_score,
            "total_incidents": s.total_incidents,
            "period_date": str(s.period_date),
        }
        for k, s in snapshots.items()
    }


@router.get("/snapshot", response_model=Optional[KPISnapshotRead], summary="Get KPI snapshot")
async def get_kpi_snapshot(
    period_type: PeriodType = Query(PeriodType.MONTHLY),
    period_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest KPI snapshot for a period."""
    if period_date is None:
        from datetime import datetime
        period_date = datetime.utcnow().date()

    snapshot = await calculate_kpi(db, period_type, period_date)
    return snapshot


@router.get("/history", summary="Get KPI history for trend charts")
async def get_kpi_history(
    period_type: PeriodType = Query(PeriodType.MONTHLY),
    limit: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KPISnapshot)
        .where(KPISnapshot.period_type == period_type.value)
        .order_by(KPISnapshot.period_date.desc())
        .limit(limit)
    )
    snapshots = result.scalars().all()
    return [
        {
            "period_date": str(s.period_date),
            "department_kpi_score": s.department_kpi_score,
            "total_incidents": s.total_incidents,
            "resolved_incidents": s.resolved_incidents,
            "repeat_incidents": s.repeat_incidents,
        }
        for s in reversed(snapshots)
    ]
