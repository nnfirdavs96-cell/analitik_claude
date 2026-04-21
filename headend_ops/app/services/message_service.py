"""Service for saving and retrieving raw Telegram messages."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import RawMessage
from app.models.user import TelegramChat, TelegramUser
from app.schemas.message import TelegramMessageIn
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_or_create_user(db: AsyncSession, msg: TelegramMessageIn) -> TelegramUser:
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == msg.user_telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = TelegramUser(
            telegram_id=msg.user_telegram_id,
            username=msg.username,
            first_name=msg.first_name,
            last_name=msg.last_name,
        )
        db.add(user)
        await db.flush()
        logger.info("user_created", telegram_id=msg.user_telegram_id)
    return user


async def get_or_create_chat(db: AsyncSession, msg: TelegramMessageIn) -> TelegramChat:
    result = await db.execute(
        select(TelegramChat).where(TelegramChat.chat_id == msg.chat_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        chat = TelegramChat(
            chat_id=msg.chat_id,
            chat_type=msg.chat_type,
            title=msg.chat_title,
        )
        db.add(chat)
        await db.flush()
        logger.info("chat_created", chat_id=msg.chat_id)
    return chat


async def save_raw_message(db: AsyncSession, msg: TelegramMessageIn) -> RawMessage:
    """Persist a raw Telegram message and its sender/chat."""
    user = await get_or_create_user(db, msg)
    chat = await get_or_create_chat(db, msg)

    raw = RawMessage(
        telegram_message_id=msg.telegram_message_id,
        chat_id=chat.id,
        user_id=user.id,
        text=msg.text,
        message_date=msg.message_date,
        parsing_status="pending",
    )
    db.add(raw)
    await db.flush()
    logger.info("raw_message_saved", message_id=raw.id, tg_message_id=msg.telegram_message_id)
    return raw


async def mark_message_processing(db: AsyncSession, message_id: int) -> None:
    result = await db.execute(select(RawMessage).where(RawMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        msg.parsing_status = "processing"
        msg.parse_attempts += 1


async def mark_message_parsed(db: AsyncSession, message_id: int) -> None:
    result = await db.execute(select(RawMessage).where(RawMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        msg.parsing_status = "parsed"
        msg.is_processed = True


async def mark_message_failed(db: AsyncSession, message_id: int, error: str) -> None:
    result = await db.execute(select(RawMessage).where(RawMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        msg.parsing_status = "failed"
        msg.parse_error = error[:2000]
