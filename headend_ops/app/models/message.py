"""Raw message model — stores original Telegram messages before parsing."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import TelegramChat, TelegramUser
    from app.models.event import ParsedEvent


class RawMessage(Base, TimestampMixin):
    """Original Telegram message as received, before any AI processing."""

    __tablename__ = "raw_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("telegram_chats.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    parsing_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_attempts: Mapped[int] = mapped_column(Integer, default=0)
    parse_error: Mapped[Optional[str]] = mapped_column(Text)
    message_date: Mapped[Optional[str]] = mapped_column(String(50))

    chat: Mapped["TelegramChat"] = relationship(back_populates="messages")
    user: Mapped[Optional["TelegramUser"]] = relationship(back_populates="messages")
    event: Mapped[Optional["ParsedEvent"]] = relationship(back_populates="raw_message", uselist=False)
