"""Schemas for ParsedEvent — the core domain object."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import EventStatus, ObjectType, RecordType, ReviewStatus, Severity


class ParsedEventBase(BaseModel):
    record_type: RecordType
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    event_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    channel_name_raw: Optional[str] = None
    object_type: Optional[ObjectType] = None
    asset_name_raw: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[EventStatus] = None
    root_cause: Optional[str] = None
    actions_taken: Optional[str] = None
    result: Optional[str] = None
    requires_followup: bool = False
    followup_note: Optional[str] = None
    repeat_issue: bool = False
    reporter_name: Optional[str] = None
    team_shift: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ParsedEventCreate(ParsedEventBase):
    raw_message_id: Optional[int] = None
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_score: Optional[int] = Field(None, ge=0, le=100)
    ai_raw_json: Optional[dict] = None
    parser_used: Optional[str] = None
    channel_id: Optional[int] = None
    asset_id: Optional[int] = None
    staff_id: Optional[int] = None
    normalization_status: str = "pending"
    review_status: str = "not_required"


class ParsedEventUpdate(BaseModel):
    record_type: Optional[RecordType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    event_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    channel_id: Optional[int] = None
    channel_name_raw: Optional[str] = None
    asset_id: Optional[int] = None
    asset_name_raw: Optional[str] = None
    object_type: Optional[ObjectType] = None
    severity: Optional[Severity] = None
    status: Optional[EventStatus] = None
    root_cause: Optional[str] = None
    actions_taken: Optional[str] = None
    result: Optional[str] = None
    requires_followup: Optional[bool] = None
    followup_note: Optional[str] = None
    repeat_issue: Optional[bool] = None
    tags: Optional[List[str]] = None
    review_status: Optional[ReviewStatus] = None
    review_note: Optional[str] = None
    reviewed_by: Optional[str] = None


class ParsedEventRead(ParsedEventBase):
    id: int
    raw_message_id: Optional[int] = None
    channel_id: Optional[int] = None
    asset_id: Optional[int] = None
    staff_id: Optional[int] = None
    ai_confidence: Optional[float] = None
    ai_score: Optional[int] = None
    parser_used: Optional[str] = None
    normalization_status: str = "pending"
    review_status: str = "not_required"
    review_note: Optional[str] = None
    repeat_issue: bool = False
    recurrence_count: int = 0
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParsedEventList(BaseModel):
    items: List[ParsedEventRead]
    total: int
    page: int
    page_size: int


class EventFilter(BaseModel):
    record_type: Optional[RecordType] = None
    severity: Optional[Severity] = None
    status: Optional[EventStatus] = None
    channel_id: Optional[int] = None
    asset_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    repeat_issue: Optional[bool] = None
    review_status: Optional[ReviewStatus] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
