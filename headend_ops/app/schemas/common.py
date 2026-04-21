"""Shared base schemas and enumerations."""
from enum import Enum


class RecordType(str, Enum):
    INCIDENT = "incident"
    WORK = "work"
    RISK = "risk"
    EQUIPMENT = "equipment"
    NOTE = "note"


class ObjectType(str, Enum):
    CHANNEL = "channel"
    NETWORK = "network"
    SERVER = "server"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    POWER = "power"
    FACILITY = "facility"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    MONITORING = "monitoring"
    CLOSED = "closed"


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReviewStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"


class ParsingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PARSED = "parsed"
    FAILED = "failed"
    SKIPPED = "skipped"
