"""
Main processing pipeline: raw message → AI parse → validate → normalize → persist.
This is the central orchestrator for the entire message-to-event flow.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.schemas import AIParseResult
from app.core.config import settings
from app.core.logging import get_logger
from app.models.event import AIReview, ParsedEvent
from app.normalization.normalizer import normalize_event_fields
from app.schemas.event import ParsedEventCreate
from app.schemas.message import IngestResponse, TelegramMessageIn
from app.services import event_service, message_service

logger = get_logger(__name__)


REVIEW_REASONS = {
    "low_confidence": "Низкая уверенность AI-парсера (< {threshold})",
    "missing_channel": "Канал не найден в справочнике",
    "missing_asset": "Оборудование не найдено в справочнике",
    "missing_severity": "Критичность не определена для инцидента",
    "fallback_used": "Использован резервный парсер вместо AI",
    "duplicate": "Возможный дубликат записи",
}


def _build_confirmation_text(event: ParsedEvent) -> str:
    """Build a short Russian confirmation message for the Telegram bot reply."""
    type_labels = {
        "incident": "ИНЦИДЕНТ",
        "work": "РАБОТА",
        "risk": "РИСК",
        "equipment": "ОБОРУДОВАНИЕ",
        "note": "ЗАМЕТКА",
    }
    severity_labels = {
        "critical": "Критическая",
        "high": "Высокая",
        "medium": "Средняя",
        "low": "Низкая",
    }
    status_labels = {
        "new": "Новый",
        "in_progress": "В работе",
        "resolved": "Устранено",
        "monitoring": "Мониторинг",
        "closed": "Закрыто",
    }

    parts = [f"✅ Сохранено: {type_labels.get(event.record_type, event.record_type)}"]

    if event.channel and event.channel.name:
        parts.append(f"Канал: {event.channel.name}")
    elif event.channel_name_raw:
        parts.append(f"Канал: {event.channel_name_raw} ⚠️")

    if event.asset and event.asset.name:
        parts.append(f"Объект: {event.asset.name}")
    elif event.asset_name_raw:
        parts.append(f"Объект: {event.asset_name_raw} ⚠️")

    if event.severity:
        parts.append(f"Критичность: {severity_labels.get(event.severity, event.severity)}")

    if event.status:
        parts.append(f"Статус: {status_labels.get(event.status, event.status)}")

    if event.repeat_issue:
        parts.append("🔁 Повторный инцидент")

    return " | ".join(parts)


def _build_review_request_text(reasons: list[str], parse_result: AIParseResult) -> str:
    """Build a Russian clarification request for the review queue bot reply."""
    lines = ["⚠️ Запись сохранена, требует уточнения:"]
    for reason in reasons:
        lines.append(f"  • {reason}")
    lines.append("")
    lines.append("Пожалуйста, проверьте запись через /pending_review")
    return "\n".join(lines)


async def process_message(
    db: AsyncSession,
    msg_in: TelegramMessageIn,
    ai_provider: AIProvider,
) -> IngestResponse:
    """
    Full pipeline for processing a single Telegram message.
    1. Save raw message
    2. Parse with AI
    3. Normalize against dictionaries
    4. Detect duplicates/recurrence
    5. Save structured event
    6. Queue for review if needed
    7. Return confirmation
    """
    # Step 1: Save raw message
    raw_msg = await message_service.save_raw_message(db, msg_in)
    await message_service.mark_message_processing(db, raw_msg.id)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        # Step 2: Parse with AI (with fallback)
        parse_result: AIParseResult = await _parse_with_fallback(
            ai_provider, msg_in.text, {"today": today}
        )

        # Step 3: Normalize channel + asset
        norm = await normalize_event_fields(
            db,
            parse_result.channel_name,
            parse_result.asset_name,
        )

        # Step 4: Build event creation payload
        event_data = ParsedEventCreate(
            raw_message_id=raw_msg.id,
            record_type=parse_result.record_type,
            title=parse_result.title,
            description=parse_result.description,
            event_datetime=_parse_dt(parse_result.event_datetime),
            end_datetime=_parse_dt(parse_result.end_datetime),
            duration_minutes=parse_result.duration_minutes,
            channel_id=norm.channel_id,
            channel_name_raw=parse_result.channel_name,
            asset_id=norm.asset_id,
            asset_name_raw=parse_result.asset_name,
            object_type=parse_result.object_type,
            severity=parse_result.severity,
            status=parse_result.status,
            root_cause=parse_result.root_cause,
            actions_taken=parse_result.actions_taken,
            result=parse_result.result,
            requires_followup=parse_result.requires_followup,
            followup_note=parse_result.followup_note,
            repeat_issue=parse_result.repeat_issue,
            reporter_name=parse_result.reporter_name,
            team_shift=parse_result.team_shift,
            ai_confidence=parse_result.ai_confidence,
            ai_score=parse_result.ai_score,
            ai_raw_json=parse_result.model_dump(),
            parser_used=ai_provider.provider_name,
            normalization_status=norm.status,
            tags=parse_result.tags,
        )

        # Step 5: Save event
        event = await event_service.create_event(db, event_data)

        # Step 6: Determine review queue status
        review_reasons = _collect_review_reasons(parse_result, norm, ai_provider.provider_name)
        if review_reasons:
            event.review_status = "pending_review"
            await _create_review_entry(db, event, review_reasons, parse_result)
            await message_service.mark_message_parsed(db, raw_msg.id)
            confirmation = _build_review_request_text(review_reasons, parse_result)
            return IngestResponse(
                message_id=raw_msg.id,
                event_id=event.id,
                status="needs_review",
                confirmation_text=confirmation,
                confidence=parse_result.ai_confidence,
            )

        event.review_status = "not_required"
        await message_service.mark_message_parsed(db, raw_msg.id)
        confirmation = _build_confirmation_text(event)

        return IngestResponse(
            message_id=raw_msg.id,
            event_id=event.id,
            status="parsed",
            confirmation_text=confirmation,
            confidence=parse_result.ai_confidence,
        )

    except Exception as e:
        logger.error("pipeline_error", error=str(e), message_id=raw_msg.id)
        await message_service.mark_message_failed(db, raw_msg.id, str(e))
        return IngestResponse(
            message_id=raw_msg.id,
            event_id=None,
            status="failed",
            confirmation_text=f"❌ Ошибка обработки сообщения. Запись сохранена для ручной проверки.",
            confidence=None,
        )


async def _parse_with_fallback(
    primary: AIProvider,
    text: str,
    context: dict,
) -> AIParseResult:
    """Try primary provider, fall back to rule-based on failure."""
    from app.ai.fallback_parser import RuleBasedFallbackParser

    try:
        return await primary.parse_message(text, context)
    except Exception as e:
        logger.warning("primary_parser_failed_using_fallback", error=str(e))
        fallback = RuleBasedFallbackParser()
        return await fallback.parse_message(text, context)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Safe datetime parsing from ISO string."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _collect_review_reasons(
    parse_result: AIParseResult,
    norm,
    parser_used: str,
) -> list[str]:
    """Determine if a record should go to the review queue."""
    reasons = []

    if parse_result.ai_confidence < settings.AI_CONFIDENCE_THRESHOLD:
        reasons.append(
            REVIEW_REASONS["low_confidence"].format(threshold=settings.AI_CONFIDENCE_THRESHOLD)
        )

    if parser_used == "fallback":
        reasons.append(REVIEW_REASONS["fallback_used"])

    if parse_result.channel_name and not norm.channel_id:
        reasons.append(REVIEW_REASONS["missing_channel"])

    if parse_result.asset_name and not norm.asset_id:
        reasons.append(REVIEW_REASONS["missing_asset"])

    if parse_result.record_type == "incident" and not parse_result.severity:
        reasons.append(REVIEW_REASONS["missing_severity"])

    return reasons


async def _create_review_entry(
    db: AsyncSession,
    event: ParsedEvent,
    reasons: list[str],
    parse_result: AIParseResult,
) -> AIReview:
    review = AIReview(
        event_id=event.id,
        reason="; ".join(reasons),
        original_json=parse_result.model_dump(),
        status="pending",
    )
    db.add(review)
    await db.flush()
    return review
