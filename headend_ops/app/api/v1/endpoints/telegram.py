"""Telegram message ingestion endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.api.deps import get_ai_provider, get_db
from app.schemas.message import IngestResponse, TelegramMessageIn
from app.services.pipeline_service import process_message

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/ingest", response_model=IngestResponse, summary="Ingest Telegram message")
async def ingest_message(
    msg: TelegramMessageIn,
    db: AsyncSession = Depends(get_db),
    ai: AIProvider = Depends(get_ai_provider),
):
    """
    Receive a Telegram message, parse it with AI, persist it as a structured event,
    and return a Russian confirmation string for the bot to send back.
    """
    return await process_message(db, msg, ai)
