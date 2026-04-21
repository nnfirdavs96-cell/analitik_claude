"""Telegram user and chat models."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.message import RawMessage


class TelegramUser(Base, TimestampMixin):
    """Telegram user who sends messages to the bot."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[Optional[str]] = mapped_column(String(200))
    last_name: Mapped[Optional[str]] = mapped_column(String(200))
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    messages: Mapped[List["RawMessage"]] = relationship(back_populates="user")

    @property
    def display_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        if parts:
            return " ".join(parts)
        return self.username or str(self.telegram_id)


class TelegramChat(Base, TimestampMixin):
    """Telegram chat (group or private) where the bot operates."""

    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    chat_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    messages: Mapped[List["RawMessage"]] = relationship(back_populates="chat")
