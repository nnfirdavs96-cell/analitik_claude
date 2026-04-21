"""Review queue endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.event import AIReview, ParsedEvent
from app.schemas.event import ParsedEventUpdate
from app.schemas.report import ReviewCorrection, ReviewQueueItem
from app.services.event_service import get_pending_reviews, update_event

router = APIRouter(prefix="/review", tags=["Review Queue"])


@router.get("/pending", response_model=List[ReviewQueueItem], summary="Get pending review items")
async def get_pending(db: AsyncSession = Depends(get_db)):
    reviews = await get_pending_reviews(db)
    return reviews


@router.post("/{review_id}/approve", summary="Approve a review item")
async def approve_review(
    review_id: int,
    resolved_by: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIReview).where(AIReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = "approved"
    review.resolved_by = resolved_by
    event = await update_event(
        db, review.event_id,
        ParsedEventUpdate(review_status="approved", reviewed_by=resolved_by)
    )
    return {"status": "approved", "event_id": review.event_id}


@router.post("/{review_id}/correct", summary="Correct and approve a review item")
async def correct_review(
    review_id: int,
    correction: ReviewCorrection,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIReview).where(AIReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = "corrected"
    review.corrected_json = correction.corrected_json
    review.resolved_by = correction.resolved_by
    review.notes = correction.notes

    # Apply corrections to the event
    update_data = {
        k: v for k, v in correction.corrected_json.items()
        if k in ParsedEventUpdate.model_fields
    }
    update_data["review_status"] = "corrected"
    update_data["reviewed_by"] = correction.resolved_by
    await update_event(db, review.event_id, ParsedEventUpdate(**update_data))

    return {"status": "corrected", "event_id": review.event_id}


@router.post("/{review_id}/reject", summary="Reject a review item")
async def reject_review(
    review_id: int,
    resolved_by: str,
    notes: str = "",
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIReview).where(AIReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = "rejected"
    review.resolved_by = resolved_by
    review.notes = notes
    await update_event(
        db, review.event_id,
        ParsedEventUpdate(review_status="rejected", reviewed_by=resolved_by)
    )
    return {"status": "rejected", "event_id": review.event_id}
