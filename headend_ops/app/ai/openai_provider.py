"""OpenAI-based AI provider for parsing and summary generation."""
import json
from typing import Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import AIProvider
from app.ai.schemas import AIParseResult, AISummaryResult
from app.core.config import settings
from app.core.exceptions import AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

PARSE_SYSTEM_PROMPT = """Ты — система анализа оперативных сообщений телевизионного головного оборудования (ТВ headend).

Твоя задача: разобрать сообщение инженера и вернуть СТРОГО JSON без каких-либо пояснений.

Правила:
- Возвращай ТОЛЬКО валидный JSON объект, без markdown, без текста вне JSON.
- Если поле неизвестно — используй null.
- Все datetime в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS).
- record_type: incident | work | risk | equipment | note
- object_type: channel | network | server | equipment | software | power | facility | other
- severity: low | medium | high | critical | null
- status: new | in_progress | resolved | monitoring | closed | null
- ai_confidence: 0.0..1.0 — твоя уверенность в разборе
- ai_score: 0..100 — оценка качества действий команды

Типичные объекты: encoder (кодировщик), transcoder (транскодер), mux (мультиплексор),
uplink (аплинк), playout, server (сервер), storage (хранилище), NMS, IRD.

Верни JSON строго по этой схеме:
{
  "record_type": "...",
  "title": "...",
  "description": "...",
  "event_datetime": "..." или null,
  "end_datetime": "..." или null,
  "duration_minutes": число или null,
  "channel_name": "..." или null,
  "object_type": "...",
  "asset_name": "..." или null,
  "severity": "..." или null,
  "status": "..." или null,
  "root_cause": "..." или null,
  "actions_taken": "..." или null,
  "result": "..." или null,
  "requires_followup": true/false,
  "followup_note": "..." или null,
  "repeat_issue": true/false,
  "reporter_name": "..." или null,
  "team_shift": "..." или null,
  "ai_confidence": 0.0..1.0,
  "ai_score": 0..100,
  "tags": ["...", "..."]
}"""

SUMMARY_SYSTEM_PROMPT = """Ты — аналитик для руководства телевизионного вещательного предприятия.

Твоя задача: на основе оперативных данных написать краткий управленческий отчёт на русском языке.

Требования:
- Язык: строго русский, деловой стиль.
- Тон: профессиональный, чёткий, без лишней воды.
- Возвращай ТОЛЬКО валидный JSON без markdown.

Схема ответа:
{
  "summary_text": "Основной текст сводки (2-4 абзаца)",
  "key_issues": ["Ключевая проблема 1", "Ключевая проблема 2"],
  "recommendations": ["Рекомендация 1", "Рекомендация 2"],
  "risk_highlights": ["Риск 1", "Риск 2"],
  "top_affected_channels": ["Канал 1", "Канал 2"],
  "top_affected_assets": ["Узел 1", "Узел 2"]
}"""


class OpenAIProvider(AIProvider):
    """Calls OpenAI ChatCompletion API for parsing and summary generation."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def provider_name(self) -> str:
        return "openai"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def parse_message(self, text: str, context: Optional[dict] = None) -> AIParseResult:
        try:
            today = context.get("today", "") if context else ""
            user_content = f"Дата операционного журнала: {today}\n\nСообщение инженера:\n{text}"

            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": PARSE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content
            if not raw_json:
                raise AIProviderError("OpenAI returned empty response")

            parsed_dict = json.loads(raw_json)
            result = AIParseResult(**parsed_dict)
            logger.info("openai_parse_success", confidence=result.ai_confidence)
            return result

        except json.JSONDecodeError as e:
            logger.error("openai_json_decode_error", error=str(e))
            raise AIProviderError(f"OpenAI returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error("openai_parse_error", error=str(e))
            raise AIProviderError(f"OpenAI parsing failed: {e}") from e

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        reraise=True,
    )
    async def generate_summary(
        self,
        events_data: list[dict],
        period_label: str,
        context: Optional[dict] = None,
    ) -> AISummaryResult:
        try:
            events_text = json.dumps(events_data, ensure_ascii=False, indent=2)
            user_content = (
                f"Период: {period_label}\n\n"
                f"Данные оперативного журнала ({len(events_data)} записей):\n{events_text}"
            )

            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content
            parsed_dict = json.loads(raw_json)
            return AISummaryResult(**parsed_dict)

        except Exception as e:
            logger.error("openai_summary_error", error=str(e))
            raise AIProviderError(f"OpenAI summary failed: {e}") from e
