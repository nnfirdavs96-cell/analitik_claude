"""Tests for AI parsing layer — schema validation and fallback parser."""
import pytest
from pydantic import ValidationError as PydanticValidationError

from app.ai.fallback_parser import RuleBasedFallbackParser
from app.ai.schemas import AIParseResult


class TestAIParseResultSchema:
    def test_valid_incident(self):
        result = AIParseResult(
            record_type="incident",
            title="Пропал звук на канале МИР",
            description="Потеря аудио на encoder-2",
            channel_name="МИР",
            asset_name="encoder-2",
            severity="high",
            status="resolved",
            ai_confidence=0.92,
            ai_score=85,
        )
        assert result.record_type == "incident"
        assert result.severity == "high"
        assert result.status == "resolved"

    def test_invalid_record_type_falls_back_to_note(self):
        result = AIParseResult(record_type="unknown_type", title="Test")
        assert result.record_type == "note"

    def test_invalid_severity_returns_none(self):
        result = AIParseResult(record_type="incident", title="Test", severity="super_critical")
        assert result.severity is None

    def test_invalid_status_returns_none(self):
        result = AIParseResult(record_type="incident", title="Test", status="done")
        assert result.status is None

    def test_confidence_clamped(self):
        result = AIParseResult(record_type="note", title="Test", ai_confidence=0.5)
        assert 0.0 <= result.ai_confidence <= 1.0

    def test_tags_truncated(self):
        result = AIParseResult(
            record_type="note",
            title="Test",
            tags=["tag" * 50, "valid_tag"],  # first tag too long
        )
        assert len(result.tags[0]) <= 100

    def test_tags_limited_to_ten(self):
        result = AIParseResult(
            record_type="note",
            title="Test",
            tags=[f"tag{i}" for i in range(15)],
        )
        assert len(result.tags) <= 10


class TestFallbackParser:
    @pytest.fixture
    def parser(self):
        return RuleBasedFallbackParser()

    @pytest.mark.asyncio
    async def test_incident_detection(self, parser):
        text = "14:20 пропал звук на канале Мир, encoder-2, перезапустили, восстановлено в 14:32"
        result = await parser.parse_message(text)
        assert result.record_type == "incident"
        assert result.ai_confidence < 0.65  # fallback always low confidence

    @pytest.mark.asyncio
    async def test_work_detection(self, parser):
        text = "Заменили блок питания на mux-1, работа завершена"
        result = await parser.parse_message(text)
        assert result.record_type in ("work", "equipment")

    @pytest.mark.asyncio
    async def test_risk_detection(self, parser):
        text = "Нагрузка на storage-1 остается высокой, риск переполнения"
        result = await parser.parse_message(text)
        assert result.record_type == "risk"

    @pytest.mark.asyncio
    async def test_channel_extraction(self, parser):
        text = "Проблема на канале МИР — потеря сигнала"
        result = await parser.parse_message(text)
        assert result.channel_name == "МИР"

    @pytest.mark.asyncio
    async def test_asset_extraction(self, parser):
        text = "Повторно завис transcoder-1, временно перезапущен сервис"
        result = await parser.parse_message(text)
        assert result.asset_name is not None
        assert "transcoder" in result.asset_name.lower()

    @pytest.mark.asyncio
    async def test_repeat_detection(self, parser):
        text = "Повторно завис сервер transcoder-1"
        result = await parser.parse_message(text)
        assert result.repeat_issue is True

    @pytest.mark.asyncio
    async def test_time_extraction(self, parser):
        text = "14:20 пропал звук, восстановлено в 14:32"
        result = await parser.parse_message(text, {"today": "2024-01-15"})
        assert result.event_datetime is not None
        assert "14:20" in result.event_datetime
        assert result.end_datetime is not None

    @pytest.mark.asyncio
    async def test_duration_calculation(self, parser):
        text = "14:20 пропал звук, восстановлено в 14:32"
        result = await parser.parse_message(text, {"today": "2024-01-15"})
        assert result.duration_minutes == 12

    @pytest.mark.asyncio
    async def test_resolved_status(self, parser):
        text = "Неисправность устранена, канал восстановлен"
        result = await parser.parse_message(text)
        assert result.status == "resolved"

    @pytest.mark.asyncio
    async def test_provider_name(self, parser):
        assert parser.provider_name == "fallback"

    @pytest.mark.asyncio
    async def test_summary_generation(self, parser):
        events = [
            {"record_type": "incident", "title": "Потеря сигнала"},
            {"record_type": "work", "title": "Замена диска"},
        ]
        summary = await parser.generate_summary(events, "Январь 2024")
        assert summary.summary_text
        assert "2" in summary.summary_text or "записей" in summary.summary_text
