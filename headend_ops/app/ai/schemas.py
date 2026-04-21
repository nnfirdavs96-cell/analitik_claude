"""AI parsing output schema — strict JSON contract between LLM and system."""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AIParseResult(BaseModel):
    """
    The structured JSON output expected from the AI parser.
    Every field is validated before the record is accepted for persistence.
    """

    record_type: str = Field(..., description="incident | work | risk | equipment | note")
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    event_datetime: Optional[str] = None   # ISO 8601 or None
    end_datetime: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    channel_name: Optional[str] = None
    object_type: Optional[str] = None
    asset_name: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    root_cause: Optional[str] = None
    actions_taken: Optional[str] = None
    result: Optional[str] = None
    requires_followup: bool = False
    followup_note: Optional[str] = None
    repeat_issue: bool = False
    reporter_name: Optional[str] = None
    team_shift: Optional[str] = None
    ai_confidence: float = Field(0.5, ge=0.0, le=1.0)
    ai_score: int = Field(50, ge=0, le=100)
    tags: List[str] = Field(default_factory=list)

    VALID_RECORD_TYPES = {"incident", "work", "risk", "equipment", "note"}
    VALID_OBJECT_TYPES = {"channel", "network", "server", "equipment", "software", "power", "facility", "other"}
    VALID_SEVERITIES = {"low", "medium", "high", "critical"}
    VALID_STATUSES = {"new", "in_progress", "resolved", "monitoring", "closed"}

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in cls.VALID_RECORD_TYPES:
            return "note"  # safe fallback
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.lower().strip()
        return v if v in cls.VALID_SEVERITIES else None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.lower().strip()
        return v if v in cls.VALID_STATUSES else None

    @field_validator("object_type")
    @classmethod
    def validate_object_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.lower().strip()
        return v if v in cls.VALID_OBJECT_TYPES else "other"

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        return [str(t).strip()[:100] for t in v if t][:10]


class AISummaryResult(BaseModel):
    """Output of the analytical AI layer for generating management summaries."""
    summary_text: str
    key_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risk_highlights: List[str] = Field(default_factory=list)
    top_affected_channels: List[str] = Field(default_factory=list)
    top_affected_assets: List[str] = Field(default_factory=list)
