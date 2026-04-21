"""Domain exceptions."""


class HeadendOpsError(Exception):
    """Base application error."""


class ParsingError(HeadendOpsError):
    """AI or rule-based parsing failed."""


class ValidationError(HeadendOpsError):
    """Parsed data failed schema validation."""


class NormalizationError(HeadendOpsError):
    """Dictionary normalization failed."""


class NotFoundError(HeadendOpsError):
    """Requested resource not found."""


class DuplicateError(HeadendOpsError):
    """Duplicate record detected."""


class ReportGenerationError(HeadendOpsError):
    """Report generation failed."""


class KPICalculationError(HeadendOpsError):
    """KPI calculation failed."""


class TelegramBotError(HeadendOpsError):
    """Telegram bot operation failed."""


class AIProviderError(HeadendOpsError):
    """External AI provider call failed."""
