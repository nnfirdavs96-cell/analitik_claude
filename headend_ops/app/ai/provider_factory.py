"""Factory that returns the active AI provider with fallback logic."""
from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.fallback_parser import RuleBasedFallbackParser
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_openai_provider() -> OpenAIProvider:
    return OpenAIProvider()


@lru_cache()
def get_fallback_provider() -> RuleBasedFallbackParser:
    return RuleBasedFallbackParser()


def get_primary_provider() -> AIProvider:
    """Return the primary AI provider based on configuration."""
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-openai-api-key-here":
        return get_openai_provider()
    logger.warning("openai_key_not_configured", fallback="rule_based")
    return get_fallback_provider()
