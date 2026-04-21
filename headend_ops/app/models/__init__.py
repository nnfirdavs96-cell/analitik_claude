"""
Model imports — ensure all models are registered with SQLAlchemy metadata.
Import order matters: base tables before tables with FK references.
"""
# Import in dependency order
from app.models.user import TelegramUser, TelegramChat
from app.models.dictionary import (
    Department, Shift, StaffMember,
    Channel, ChannelAlias,
    Asset, AssetAlias,
    IncidentCategory, RootCauseCategory,
)
from app.models.message import RawMessage
from app.models.event import ParsedEvent, AIReview
from app.models.kpi import KPISnapshot
from app.models.report import Report, ReportItem, AuditLog, AppSetting

__all__ = [
    "TelegramUser", "TelegramChat",
    "Department", "Shift", "StaffMember",
    "Channel", "ChannelAlias",
    "Asset", "AssetAlias",
    "IncidentCategory", "RootCauseCategory",
    "RawMessage",
    "ParsedEvent", "AIReview",
    "KPISnapshot",
    "Report", "ReportItem", "AuditLog", "AppSetting",
]
