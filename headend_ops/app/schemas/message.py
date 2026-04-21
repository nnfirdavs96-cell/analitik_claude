"""Schemas for raw messages and Telegram ingestion."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelegramMessageIn(BaseModel):
    """Incoming Telegram message payload for ingestion endpoint."""
    telegram_message_id: int
    chat_id: int
    chat_type: str
    chat_title: Optional[str] = None
    user_telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    text: str = Field(..., min_length=1)
    message_date: Optional[str] = None


class RawMessageRead(BaseModel):
    id: int
    telegram_message_id: int
    text: str
    parsing_status: str
    is_processed: bool
    parse_attempts: int
    parse_error: Optional[str] = None
    message_date: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    """Response returned after ingesting a Telegram message."""
    message_id: int
    event_id: Optional[int] = None
    status: str  # parsed | needs_review | failed
    confirmation_text: str  # Russian confirmation for the bot
    confidence: Optional[float] = None
