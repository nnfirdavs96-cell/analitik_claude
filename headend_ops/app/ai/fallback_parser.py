"""Rule-based fallback parser used when OpenAI is unavailable."""
import re
from datetime import datetime, date
from typing import Optional

from app.ai.base import AIProvider
from app.ai.schemas import AIParseResult, AISummaryResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Keyword maps for classification
INCIDENT_KEYWORDS = {
    "пропал", "пропало", "авария", "сбой", "отказ", "не работает",
    "упал", "упало", "зависл", "прервал", "прерывание", "проблема",
    "ошибка", "критическ", "авар", "нет сигнала", "потеря сигнала",
    "выход из строя", "перегрев", "перегруз",
}

WORK_KEYWORDS = {
    "замен", "установил", "настроил", "обновил", "перезапустил",
    "выполнен", "завершен", "произведен", "проверил", "плановое",
    "обслуживание", "техническое", "работа завершена", "настройка",
    "конфигурация", "монтаж", "ТО", "профилактика",
}

RISK_KEYWORDS = {
    "риск", "нагрузка высокая", "заполнен", "нестабильн",
    "ненадёжн", "ненадежн", "устарел", "изношен", "вероятн",
    "может отказать", "ведём мониторинг", "ведем мониторинг",
    "наблюдаются потери", "потенциальный",
}

EQUIPMENT_KEYWORDS = {
    "блок питания", "оборудование", "диск", "плата", "модуль",
    "диагностик", "замена оборудования", "новый", "установлен",
}

SEVERITY_MAP = {
    "критическ": "critical",
    "высок": "high",
    "серьёзн": "high",
    "серьезн": "high",
    "средн": "medium",
    "незначительн": "low",
    "низк": "low",
    "минимальн": "low",
}

STATUS_RESOLVED = {"устранен", "восстановлен", "решен", "завершен", "выполнен", "исправлен"}
STATUS_IN_PROGRESS = {"ведётся", "ведется", "в процессе", "продолжается", "диагностируется"}
STATUS_MONITORING = {"мониторинг", "наблюдаем", "наблюдается", "ведём наблюдение", "под контролем"}

TIME_PATTERN = re.compile(r'\b(\d{1,2}):(\d{2})\b')
DURATION_PATTERN = re.compile(r'(\d+)\s*мин(?:ут)?')


def _detect_record_type(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in RISK_KEYWORDS):
        return "risk"
    if any(kw in text_lower for kw in EQUIPMENT_KEYWORDS):
        return "equipment"
    if any(kw in text_lower for kw in WORK_KEYWORDS):
        return "work"
    if any(kw in text_lower for kw in INCIDENT_KEYWORDS):
        return "incident"
    return "note"


def _detect_severity(text: str) -> Optional[str]:
    text_lower = text.lower()
    for keyword, severity in SEVERITY_MAP.items():
        if keyword in text_lower:
            return severity
    # Infer from incident words
    if any(w in text_lower for w in ("авария", "критическ", "аварийн")):
        return "critical"
    if any(w in text_lower for w in ("пропал", "отказ", "нет сигнала")):
        return "high"
    return None


def _detect_status(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in STATUS_RESOLVED):
        return "resolved"
    if any(w in text_lower for w in STATUS_IN_PROGRESS):
        return "in_progress"
    if any(w in text_lower for w in STATUS_MONITORING):
        return "monitoring"
    return "new"


def _extract_channel_name(text: str) -> Optional[str]:
    """Extract channel name — looks for known patterns."""
    patterns = [
        r'канал[е\s]+([А-ЯЁа-яёA-Za-z][А-ЯЁа-яёA-Za-z0-9\-\s]{1,30}?)(?:\s*[,.]|\s+[а-яА-Я])',
        r'на\s+канале?\s+([А-ЯЁа-яёA-Za-z][А-ЯЁа-яёA-Za-z0-9\-\s]{1,20}?)(?:\s*[,.])',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    # Look for known channel name fragments
    known = ["МИР", "Мир", "MIR", "Россия", "Первый", "НТВ", "ТНТ", "РЕН", "СТС", "МАТЧ", "СПАС"]
    for ch in known:
        if ch in text:
            return ch
    return None


def _extract_asset_name(text: str) -> Optional[str]:
    """Extract asset/equipment name from text."""
    patterns = [
        r'(encoder[-\s]?\d+)',
        r'(transcoder[-\s]?\d+)',
        r'(mux[-\s]?\d+)',
        r'(playout[-\s]?\d+)',
        r'(server[-\s]?\d+)',
        r'(storage[-\s]?\d+)',
        r'(uplink[-\s]?\d*)',
        r'(NMS[-\s]?\d*)',
        r'(IRD[-\s]?\d+)',
        r'(кодер[-\s]?\d+)',
        r'(транскодер[-\s]?\d+)',
        r'(мультиплексор[-\s]?\d+)',
        r'(аплинк[-\s]?\d*)',
        r'(сервер[-\s]?\d+)',
        r'(хранилищ[еа][-\s]?\d*)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_times(text: str, today: Optional[date] = None) -> tuple[Optional[str], Optional[str]]:
    """Extract start and end times from text."""
    times = TIME_PATTERN.findall(text)
    if not times:
        return None, None
    base_date = today or datetime.now().date()
    start_str = f"{base_date}T{times[0][0].zfill(2)}:{times[0][1]}:00"
    end_str = None
    if len(times) >= 2:
        end_str = f"{base_date}T{times[1][0].zfill(2)}:{times[1][1]}:00"
    return start_str, end_str


def _extract_duration(text: str) -> Optional[int]:
    m = DURATION_PATTERN.search(text)
    if m:
        return int(m.group(1))
    return None


def _build_title(text: str, record_type: str) -> str:
    """Build a short title from the message text."""
    first_sentence = re.split(r'[.!?\n]', text.strip())[0].strip()
    return first_sentence[:200] if first_sentence else text[:200]


def _detect_repeat(text: str) -> bool:
    repeat_words = ["повторно", "снова", "опять", "вновь", "ещё раз", "еще раз", "в очередной раз"]
    return any(w in text.lower() for w in repeat_words)


def _detect_followup(text: str) -> bool:
    followup_words = ["нужно", "необходимо", "требуется", "следует", "рекомендуется", "запланировать"]
    return any(w in text.lower() for w in followup_words)


class RuleBasedFallbackParser(AIProvider):
    """
    Deterministic rule-based parser.
    Used when OpenAI is unavailable or rate-limited.
    Produces lower-confidence results that typically go to review queue.
    """

    @property
    def provider_name(self) -> str:
        return "fallback"

    async def parse_message(self, text: str, context: Optional[dict] = None) -> AIParseResult:
        today_str = context.get("today") if context else None
        today = None
        if today_str:
            try:
                today = date.fromisoformat(today_str[:10])
            except ValueError:
                pass

        record_type = _detect_record_type(text)
        severity = _detect_severity(text)
        status = _detect_status(text)
        channel_name = _extract_channel_name(text)
        asset_name = _extract_asset_name(text)
        start_time, end_time = _extract_times(text, today)
        duration = _extract_duration(text)
        repeat = _detect_repeat(text)
        followup = _detect_followup(text)
        title = _build_title(text, record_type)

        # Infer duration from times
        if not duration and start_time and end_time:
            try:
                s = datetime.fromisoformat(start_time)
                e = datetime.fromisoformat(end_time)
                diff = (e - s).total_seconds() / 60
                if 0 < diff < 1440:
                    duration = int(diff)
            except ValueError:
                pass

        # Object type
        object_type = "other"
        if channel_name:
            object_type = "channel"
        elif asset_name:
            text_lower = text.lower()
            if any(w in text_lower for w in ("сервер", "server")):
                object_type = "server"
            elif any(w in text_lower for w in ("сеть", "network", "uplink", "аплинк")):
                object_type = "network"
            else:
                object_type = "equipment"

        # Confidence is always low for fallback parser
        confidence = 0.40

        logger.info("fallback_parse", record_type=record_type, confidence=confidence)

        return AIParseResult(
            record_type=record_type,
            title=title,
            description=text[:1000],
            event_datetime=start_time,
            end_datetime=end_time,
            duration_minutes=duration,
            channel_name=channel_name,
            object_type=object_type,
            asset_name=asset_name,
            severity=severity,
            status=status,
            root_cause=None,
            actions_taken=None,
            result=None,
            requires_followup=followup,
            followup_note=None,
            repeat_issue=repeat,
            reporter_name=None,
            team_shift=None,
            ai_confidence=confidence,
            ai_score=35,
            tags=[],
        )

    async def generate_summary(
        self,
        events_data: list[dict],
        period_label: str,
        context: Optional[dict] = None,
    ) -> AISummaryResult:
        """Minimal template-based fallback summary."""
        total = len(events_data)
        incidents = [e for e in events_data if e.get("record_type") == "incident"]
        works = [e for e in events_data if e.get("record_type") == "work"]
        risks = [e for e in events_data if e.get("record_type") == "risk"]

        summary = (
            f"Сводка за период: {period_label}.\n"
            f"Всего записей: {total}. "
            f"Инциденты: {len(incidents)}, работы: {len(works)}, риски: {len(risks)}.\n"
            f"Подробный анализ недоступен (используется резервный парсер)."
        )

        return AISummaryResult(
            summary_text=summary,
            key_issues=[e.get("title", "")[:100] for e in incidents[:3]],
            recommendations=["Обеспечить доступность AI-провайдера для полного анализа"],
            risk_highlights=[e.get("title", "")[:100] for e in risks[:3]],
            top_affected_channels=[],
            top_affected_assets=[],
        )
