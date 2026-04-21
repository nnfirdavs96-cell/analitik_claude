"""Core ParsedEvent model — the structured operational record."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer,
    String, Text, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.message import RawMessage
    from app.models.dictionary import Channel, Asset, StaffMember


class ParsedEvent(Base, TimestampMixin):
    """
    Structured operational event extracted from a raw Telegram message.
    This is the core domain entity.
    """

    __tablename__ = "parsed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("raw_messages.id"), unique=True
    )

    # Classification
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    event_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Channel / Asset references
    channel_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("channels.id"))
    channel_name_raw: Mapped[Optional[str]] = mapped_column(String(200))
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("assets.id"))
    asset_name_raw: Mapped[Optional[str]] = mapped_column(String(200))
    object_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Severity / Status
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(50))

    # Technical details
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    actions_taken: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[str]] = mapped_column(Text)

    # Follow-up
    requires_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    followup_note: Mapped[Optional[str]] = mapped_column(Text)

    # Recurrence / duplicate detection
    repeat_issue: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("parsed_events.id"))

    # Reporter
    reporter_name: Mapped[Optional[str]] = mapped_column(String(200))
    team_shift: Mapped[Optional[str]] = mapped_column(String(100))
    staff_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff_members.id"))

    # AI metadata
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer)
    ai_raw_json: Mapped[Optional[dict]] = mapped_column(JSON)
    parser_used: Mapped[Optional[str]] = mapped_column(String(50))

    # Normalization
    normalization_status: Mapped[str] = mapped_column(String(50), default="pending")

    # Review queue
    review_status: Mapped[str] = mapped_column(String(50), default="not_required")
    review_note: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(200))

    # Tags
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Relationships
    raw_message: Mapped[Optional["RawMessage"]] = relationship(back_populates="event")
    channel: Mapped[Optional["Channel"]] = relationship(back_populates="events")
    asset: Mapped[Optional["Asset"]] = relationship(back_populates="events")
    ai_review: Mapped[Optional["AIReview"]] = relationship(back_populates="event", uselist=False)


class AIReview(Base, TimestampMixin):
    """Review queue entry for low-confidence or ambiguous parsed events."""

    __tablename__ = "ai_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("parsed_events.id"), unique=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    original_json: Mapped[Optional[dict]] = mapped_column(JSON)
    corrected_json: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    resolved_by: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    event: Mapped["ParsedEvent"] = relationship(back_populates="ai_review")
