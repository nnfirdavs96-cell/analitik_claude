"""Events CRUD and listing endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.common import EventStatus, RecordType, ReviewStatus, Severity
from app.schemas.event import EventFilter, ParsedEventList, ParsedEventRead, ParsedEventUpdate
from app.services.event_service import get_event, list_events, update_event

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=ParsedEventList, summary="List events with filters")
async def list_events_endpoint(
    record_type: Optional[RecordType] = Query(None),
    severity: Optional[Severity] = Query(None),
    status: Optional[EventStatus] = Query(None),
    channel_id: Optional[int] = Query(None),
    asset_id: Optional[int] = Query(None),
    repeat_issue: Optional[bool] = Query(None),
    review_status: Optional[ReviewStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    filters = EventFilter(
        record_type=record_type,
        severity=severity,
        status=status,
        channel_id=channel_id,
        asset_id=asset_id,
        repeat_issue=repeat_issue,
        review_status=review_status,
        page=page,
        page_size=page_size,
    )
    events, total = await list_events(db, filters)
    return ParsedEventList(items=events, total=total, page=page, page_size=page_size)


@router.get("/{event_id}", response_model=ParsedEventRead, summary="Get event by ID")
async def get_event_endpoint(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/{event_id}", response_model=ParsedEventRead, summary="Update event fields")
async def update_event_endpoint(
    event_id: int,
    data: ParsedEventUpdate,
    db: AsyncSession = Depends(get_db),
):
    event = await update_event(db, event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
