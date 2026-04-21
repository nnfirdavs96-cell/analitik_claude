"""Service for creating, reading, and updating ParsedEvents."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import AIReview, ParsedEvent
from app.schemas.event import EventFilter, ParsedEventCreate, ParsedEventUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)

DUPLICATE_WINDOW_HOURS = 2
RECURRENCE_WINDOW_DAYS = 30


async def create_event(db: AsyncSession, data: ParsedEventCreate) -> ParsedEvent:
    """Persist a new parsed event and check for duplicates/recurrence."""
    event = ParsedEvent(**data.model_dump())
    db.add(event)
    await db.flush()

    # Duplicate / recurrence detection
    await _check_and_mark_recurrence(db, event)

    logger.info("event_created", event_id=event.id, record_type=event.record_type)
    return event


async def get_event(db: AsyncSession, event_id: int) -> Optional[ParsedEvent]:
    result = await db.execute(
        select(ParsedEvent)
        .options(selectinload(ParsedEvent.channel), selectinload(ParsedEvent.asset))
        .where(ParsedEvent.id == event_id)
    )
    return result.scalar_one_or_none()


async def update_event(
    db: AsyncSession, event_id: int, data: ParsedEventUpdate
) -> Optional[ParsedEvent]:
    event = await get_event(db, event_id)
    if not event:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(event, field, value)
    await db.flush()
    return event


async def list_events(db: AsyncSession, filters: EventFilter) -> tuple[list[ParsedEvent], int]:
    """Return filtered events with total count for pagination."""
    query = select(ParsedEvent).options(
        selectinload(ParsedEvent.channel),
        selectinload(ParsedEvent.asset),
    )

    conditions = []
    if filters.record_type:
        conditions.append(ParsedEvent.record_type == filters.record_type)
    if filters.severity:
        conditions.append(ParsedEvent.severity == filters.severity)
    if filters.status:
        conditions.append(ParsedEvent.status == filters.status)
    if filters.channel_id:
        conditions.append(ParsedEvent.channel_id == filters.channel_id)
    if filters.asset_id:
        conditions.append(ParsedEvent.asset_id == filters.asset_id)
    if filters.date_from:
        conditions.append(ParsedEvent.created_at >= filters.date_from)
    if filters.date_to:
        conditions.append(ParsedEvent.created_at <= filters.date_to)
    if filters.repeat_issue is not None:
        conditions.append(ParsedEvent.repeat_issue == filters.repeat_issue)
    if filters.review_status:
        conditions.append(ParsedEvent.review_status == filters.review_status)

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginate
    offset = (filters.page - 1) * filters.page_size
    query = query.order_by(ParsedEvent.created_at.desc()).offset(offset).limit(filters.page_size)
    result = await db.execute(query)
    events = result.scalars().all()

    return list(events), total


async def _check_and_mark_recurrence(db: AsyncSession, event: ParsedEvent) -> None:
    """Detect if this event is a repeat of a recent similar incident."""
    if event.record_type not in ("incident", "equipment"):
        return

    window_start = datetime.utcnow() - timedelta(days=RECURRENCE_WINDOW_DAYS)

    # Look for similar events on same asset or channel
    conditions = [
        ParsedEvent.id != event.id,
        ParsedEvent.created_at >= window_start,
        ParsedEvent.record_type == event.record_type,
        ParsedEvent.is_duplicate == False,
    ]

    asset_or_channel = []
    if event.asset_id:
        asset_or_channel.append(ParsedEvent.asset_id == event.asset_id)
    if event.channel_id:
        asset_or_channel.append(ParsedEvent.channel_id == event.channel_id)

    if not asset_or_channel:
        return

    conditions.append(or_(*asset_or_channel))

    result = await db.execute(
        select(ParsedEvent)
        .where(and_(*conditions))
        .order_by(ParsedEvent.created_at.desc())
    )
    similar = result.scalars().all()

    if similar:
        event.repeat_issue = True
        event.recurrence_count = len(similar)

        # Check for near-duplicate in short window
        recent_window = datetime.utcnow() - timedelta(hours=DUPLICATE_WINDOW_HOURS)
        near_duplicates = [s for s in similar if s.created_at >= recent_window]
        if near_duplicates:
            event.is_duplicate = True
            event.duplicate_of_id = near_duplicates[0].id
            logger.info(
                "duplicate_detected",
                event_id=event.id,
                original_id=near_duplicates[0].id,
            )


async def get_pending_reviews(db: AsyncSession) -> list[AIReview]:
    result = await db.execute(
        select(AIReview)
        .options(selectinload(AIReview.event))
        .where(AIReview.status == "pending")
        .order_by(AIReview.created_at.asc())
    )
    return list(result.scalars().all())
