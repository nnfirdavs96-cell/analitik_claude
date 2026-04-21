"""Handler for free-form text messages — the core operational logging flow."""
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import Message

import httpx

from app.bot import texts
from app.core.config import settings
from app.core.logging import get_logger

router = Router()
logger = get_logger(__name__)

API_BASE = f"http://{settings.API_HOST if settings.API_HOST != '0.0.0.0' else 'localhost'}:{settings.API_PORT}{settings.API_PREFIX}"

MIN_MESSAGE_LENGTH = 10  # ignore very short messages


def _should_process(message: Message) -> bool:
    """Decide whether to process this message."""
    if not message.text:
        return False
    text = message.text.strip()
    if text.startswith("/"):
        return False
    if len(text) < MIN_MESSAGE_LENGTH:
        return False
    return True


@router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """
    Core handler: receives any text message, calls the ingest API,
    and replies with a Russian confirmation.
    """
    if not _should_process(message):
        return

    user = message.from_user
    chat = message.chat

    logger.info(
        "message_received",
        chat_id=chat.id,
        user_id=user.id if user else None,
        text_len=len(message.text or ""),
    )

    # Build the ingest payload
    payload = {
        "telegram_message_id": message.message_id,
        "chat_id": chat.id,
        "chat_type": chat.type,
        "chat_title": chat.title,
        "user_telegram_id": user.id if user else 0,
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
        "last_name": user.last_name if user else None,
        "text": message.text,
        "message_date": datetime.now(timezone.utc).isoformat(),
    }

    # Show processing indicator for longer messages
    processing_msg = None
    if len(message.text) > 100:
        processing_msg = await message.reply(texts.PARSING_IN_PROGRESS)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{API_BASE}/telegram/ingest",
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()

        confirmation = result.get("confirmation_text", texts.PARSE_FAILED)

        if processing_msg:
            await processing_msg.edit_text(confirmation, parse_mode="HTML")
        else:
            await message.reply(confirmation, parse_mode="HTML")

    except httpx.HTTPError as e:
        logger.error("ingest_api_error", error=str(e))
        reply_text = texts.PARSE_FAILED
        if processing_msg:
            await processing_msg.edit_text(reply_text)
        else:
            await message.reply(reply_text)
    except Exception as e:
        logger.error("message_handler_error", error=str(e))
        if processing_msg:
            await processing_msg.edit_text(texts.PARSE_FAILED)
