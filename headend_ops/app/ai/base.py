"""Abstract AI provider interface."""
from abc import ABC, abstractmethod
from typing import Optional

from app.ai.schemas import AIParseResult, AISummaryResult


class AIProvider(ABC):
    """
    Abstract base for AI parsing providers.
    Implementations: OpenAIProvider, RuleBasedFallbackParser.
    """

    @abstractmethod
    async def parse_message(self, text: str, context: Optional[dict] = None) -> AIParseResult:
        """
        Parse a natural-language operational message into a structured AIParseResult.
        Must always return a valid AIParseResult, never raise for parse failures.
        """

    @abstractmethod
    async def generate_summary(
        self,
        events_data: list[dict],
        period_label: str,
        context: Optional[dict] = None,
    ) -> AISummaryResult:
        """Generate a management summary for the given events data."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier for logging and audit."""
