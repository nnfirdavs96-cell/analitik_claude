"""All Russian user-facing text for the Telegram bot."""

WELCOME = """
👋 Добро пожаловать в систему оперативного учёта!

Я помогу вашей команде вести журнал технических событий прямо в этом чате.

Просто напишите, что произошло, и я автоматически:
• разберу сообщение с помощью AI
• внесу данные в базу
• сформирую отчёт для руководства

Введите /help для списка команд.
"""

HELP = """
📋 <b>Команды бота</b>

<b>Запись событий:</b>
/incident — зафиксировать инцидент
/work — зафиксировать выполненную работу
/risk — зафиксировать риск
/equipment — записать состояние оборудования
/note — добавить наблюдение или заметку

<b>Отчёты:</b>
/report_day — ежедневный отчёт
/report_week — еженедельный отчёт
/report_month — ежемесячный отчёт
/kpi — текущие KPI

<b>Справочники:</b>
/channels — список каналов
/assets — список оборудования

<b>Контроль:</b>
/pending_review — записи, требующие уточнения

💡 <b>Совет:</b> Вы можете просто написать текстом — система разберёт его автоматически.
Пример: <i>«14:20 пропал звук на канале Мир, encoder-2, перезапустили, восстановлено в 14:32»</i>
"""

PARSING_IN_PROGRESS = "⏳ Обрабатываю запись..."

PARSE_FAILED = (
    "❌ Не удалось обработать сообщение. Запись сохранена для ручного разбора.\n"
    "Используйте /pending_review для проверки."
)

NO_EVENTS_TODAY = "📭 Сегодня событий не зафиксировано."

REPORT_GENERATING = "⏳ Формирую отчёт, подождите..."

REPORT_READY = "✅ Отчёт готов. Скачайте через веб-панель: {url}"

REPORT_FAILED = "❌ Ошибка при формировании отчёта. Попробуйте позже."

KPI_HEADER = "📊 <b>KPI отдела за текущий месяц</b>\n"

CHANNELS_HEADER = "📺 <b>Каналы в системе:</b>\n"

ASSETS_HEADER = "⚙️ <b>Оборудование в системе:</b>\n"

PENDING_REVIEW_HEADER = "🔍 <b>Записи, требующие проверки:</b>\n"

NO_PENDING_REVIEWS = "✅ Нет записей, требующих проверки."

INCIDENT_PROMPT = (
    "📝 Опишите инцидент в свободной форме.\n\n"
    "Укажите по возможности:\n"
    "• что произошло\n"
    "• когда (время)\n"
    "• какой канал или оборудование\n"
    "• что было сделано\n"
    "• каков результат"
)

WORK_PROMPT = (
    "🔧 Опишите выполненную работу.\n\n"
    "Укажите:\n"
    "• что было сделано\n"
    "• какое оборудование\n"
    "• результат"
)

RISK_PROMPT = (
    "⚠️ Опишите выявленный риск.\n\n"
    "Укажите:\n"
    "• в чём заключается риск\n"
    "• какое оборудование/канал\n"
    "• рекомендуемые действия"
)

EQUIPMENT_PROMPT = (
    "🖥️ Опишите состояние оборудования.\n\n"
    "Укажите:\n"
    "• оборудование\n"
    "• текущее состояние\n"
    "• выполненные действия"
)

NOTE_PROMPT = (
    "📌 Напишите наблюдение или заметку."
)

def kpi_message(kpi: dict) -> str:
    score = kpi.get("department_kpi_score")
    score_str = f"{score:.1f}" if score is not None else "—"

    emoji = "🟢" if score and score >= 75 else ("🟡" if score and score >= 50 else "🔴")

    return (
        f"📊 <b>KPI отдела за текущий месяц</b>\n\n"
        f"{emoji} <b>Итоговый KPI: {score_str} / 100</b>\n\n"
        f"Инциденты: {kpi.get('total_incidents', 0)} "
        f"(критических: {kpi.get('critical_incidents', 0)})\n"
        f"Устранено: {kpi.get('resolved_incidents', 0)}, "
        f"не устранено: {kpi.get('unresolved_incidents', 0)}\n"
        f"Повторных инцидентов: {kpi.get('repeat_incidents', 0)}\n"
        f"Работ выполнено: {kpi.get('total_works', 0)}\n"
        f"Среднее время устранения: "
        f"{kpi.get('average_resolution_time_minutes') or '—'} мин\n\n"
        f"Подробнее: /report_month"
    )


def pending_reviews_message(reviews: list) -> str:
    if not reviews:
        return NO_PENDING_REVIEWS
    lines = [PENDING_REVIEW_HEADER]
    for r in reviews[:10]:
        lines.append(f"• #{r['id']} — {r['reason'][:80]}")
    if len(reviews) > 10:
        lines.append(f"...и ещё {len(reviews) - 10}")
    lines.append("\nПроверьте через веб-панель /api/v1/review/pending")
    return "\n".join(lines)
