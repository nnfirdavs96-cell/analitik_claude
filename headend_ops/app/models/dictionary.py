"""Master dictionary models: channels, assets, categories, etc."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Channel(Base, TimestampMixin):
    """TV channel (broadcast channel)."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ru: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    aliases: Mapped[List["ChannelAlias"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    events: Mapped[List["ParsedEvent"]] = relationship(back_populates="channel")


class ChannelAlias(Base):
    """Alternative names / aliases for channels used during normalization."""

    __tablename__ = "channel_aliases"
    __table_args__ = (UniqueConstraint("channel_id", "alias", name="uq_channel_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey("channels.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(200), nullable=False)

    channel: Mapped["Channel"] = relationship(back_populates="aliases")


class Asset(Base, TimestampMixin):
    """Physical or logical asset (encoder, server, mux, uplink, etc.)."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # encoder, server, mux, etc.
    location: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    aliases: Mapped[List["AssetAlias"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    events: Mapped[List["ParsedEvent"]] = relationship(back_populates="asset")


class AssetAlias(Base):
    """Alternative names for assets used during normalization."""

    __tablename__ = "asset_aliases"
    __table_args__ = (UniqueConstraint("asset_id", "alias", name="uq_asset_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(200), nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="aliases")


class Department(Base, TimestampMixin):
    """Organizational department."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    staff: Mapped[List["StaffMember"]] = relationship(back_populates="department")


class Shift(Base, TimestampMixin):
    """Work shift / team rotation."""

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffMember(Base, TimestampMixin):
    """Operations staff member."""

    __tablename__ = "staff_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100))
    telegram_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department: Mapped[Optional["Department"]] = relationship(back_populates="staff")


class IncidentCategory(Base, TimestampMixin):
    """Categorization for incidents and works."""

    __tablename__ = "incident_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)  # incident, work, risk, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class RootCauseCategory(Base, TimestampMixin):
    """Root cause categorization for incidents."""

    __tablename__ = "root_cause_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


if TYPE_CHECKING:
    from app.models.event import ParsedEvent
