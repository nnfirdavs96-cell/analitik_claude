"""Report generation and export endpoints."""
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.report import Report
from app.reports.generator import generate_report
from app.schemas.common import PeriodType
from app.schemas.report import ReportRead, ReportRequest

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportRead, summary="Generate report")
async def generate_report_endpoint(
    req: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a report for the specified period synchronously."""
    report = await generate_report(
        db,
        req.report_type,
        req.period_start,
        req.generate_excel,
        req.generate_pdf,
        req.generate_ai_summary,
    )
    return report


@router.get("", summary="List reports")
async def list_reports(
    report_type: Optional[PeriodType] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Report).order_by(Report.created_at.desc()).limit(limit)
    if report_type:
        query = query.where(Report.report_type == report_type.value)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportRead, summary="Get report by ID")
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download/excel", summary="Download Excel report")
async def download_excel(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.excel_path or not Path(report.excel_path).exists():
        raise HTTPException(status_code=404, detail="Excel file not available")
    return FileResponse(
        path=report.excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(report.excel_path).name,
    )


@router.get("/{report_id}/download/pdf", summary="Download PDF report")
async def download_pdf(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.pdf_path or not Path(report.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not available")
    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=Path(report.pdf_path).name,
    )
