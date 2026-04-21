"""Excel report exporter using openpyxl."""
from datetime import datetime
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import (
    Alignment, Border, Font, PatternFill, Side
)
from openpyxl.utils import get_column_letter

# Colour palette
HEADER_FILL = PatternFill("solid", fgColor="1F3864")  # dark blue
SUBHEADER_FILL = PatternFill("solid", fgColor="2E75B6")
ACCENT_FILL = PatternFill("solid", fgColor="D6E4F0")
ALT_ROW_FILL = PatternFill("solid", fgColor="EBF3FB")
KPI_GOOD_FILL = PatternFill("solid", fgColor="C6EFCE")
KPI_MED_FILL = PatternFill("solid", fgColor="FFEB9C")
KPI_BAD_FILL = PatternFill("solid", fgColor="FFC7CE")

WHITE_FONT = Font(color="FFFFFF", bold=True, size=11)
BOLD_FONT = Font(bold=True, size=11)
NORMAL_FONT = Font(size=10)

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

SEVERITY_LABELS = {"critical": "Критическая", "high": "Высокая", "medium": "Средняя", "low": "Низкая"}
STATUS_LABELS = {
    "new": "Новый", "in_progress": "В работе", "resolved": "Устранено",
    "monitoring": "Мониторинг", "closed": "Закрыто",
}
TYPE_LABELS = {
    "incident": "Инцидент", "work": "Работа", "risk": "Риск",
    "equipment": "Оборудование", "note": "Заметка",
}


def _header_cell(ws, row: int, col: int, value: str, width: int = None) -> None:
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = WHITE_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = THIN_BORDER
    if width and ws.column_dimensions:
        ws.column_dimensions[get_column_letter(col)].width = width


def _kpi_score_fill(score: Any) -> PatternFill:
    if score is None:
        return ACCENT_FILL
    if score >= 75:
        return KPI_GOOD_FILL
    if score >= 50:
        return KPI_MED_FILL
    return KPI_BAD_FILL


def _build_dashboard_sheet(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("Дашборд")
    ws.sheet_view.showGridLines = False

    kpi = data.get("kpi", {})
    stats = data.get("stats", {})

    ws.merge_cells("A1:F1")
    title_cell = ws["A1"]
    title_cell.value = data.get("period_label", "Оперативный отчёт")
    title_cell.font = Font(bold=True, size=16, color="1F3864")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("A2:F2")
    gen_cell = ws["A2"]
    gen_cell.value = f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    gen_cell.font = Font(size=10, color="808080")
    gen_cell.alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 20

    # KPI block header
    ws.merge_cells("A4:F4")
    ws["A4"].value = "КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ ЭФФЕКТИВНОСТИ"
    ws["A4"].font = Font(bold=True, size=12, color="FFFFFF")
    ws["A4"].fill = SUBHEADER_FILL
    ws["A4"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[4].height = 25

    kpi_rows = [
        ("Итоговый KPI отдела", kpi.get("department_kpi_score")),
        ("Оценка инцидентов", kpi.get("incident_score")),
        ("Оценка устранения", kpi.get("resolution_score")),
        ("Оценка работ", kpi.get("work_completion_score")),
        ("Оценка повторных проблем", kpi.get("repeat_issue_score")),
        ("Оценка AI-качества", kpi.get("ai_quality_score")),
    ]

    for i, (label, value) in enumerate(kpi_rows, start=5):
        row = 4 + i
        ws.cell(row=row, column=1, value=label).font = BOLD_FONT
        score_cell = ws.cell(row=row, column=2, value=round(value, 1) if value else "—")
        score_cell.fill = _kpi_score_fill(value)
        score_cell.font = Font(bold=True, size=11)
        score_cell.alignment = Alignment(horizontal="center")
        score_cell.border = THIN_BORDER

    # Stats block
    ws.merge_cells("A12:F12")
    ws["A12"].value = "СТАТИСТИКА ЗА ПЕРИОД"
    ws["A12"].font = Font(bold=True, size=12, color="FFFFFF")
    ws["A12"].fill = SUBHEADER_FILL
    ws["A12"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[12].height = 25

    stat_rows = [
        ("Всего записей", stats.get("total_events", 0)),
        ("Инцидентов", stats.get("total_incidents", 0)),
        ("Критических инцидентов", stats.get("critical_incidents", 0)),
        ("Устранено инцидентов", stats.get("resolved_incidents", 0)),
        ("Не устранено", stats.get("unresolved_incidents", 0)),
        ("Повторных инцидентов", stats.get("repeat_incidents", 0)),
        ("Работ выполнено", stats.get("total_works", 0)),
        ("Рисков", stats.get("total_risks", 0)),
        ("Открытых последействий", stats.get("followups_open", 0)),
        ("Среднее время устранения (мин)", stats.get("avg_resolution_minutes", "—")),
    ]

    for i, (label, value) in enumerate(stat_rows, start=13):
        ws.cell(row=i, column=1, value=label).font = NORMAL_FONT
        val_cell = ws.cell(row=i, column=2, value=value)
        val_cell.alignment = Alignment(horizontal="center")
        if i % 2 == 0:
            ws.cell(row=i, column=1).fill = ALT_ROW_FILL
            val_cell.fill = ALT_ROW_FILL

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 18


def _build_events_sheet(
    wb: Workbook, sheet_name: str, events: list[dict], columns: list[tuple]
) -> None:
    ws = wb.create_sheet(sheet_name)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}1"

    for col_idx, (header, key, width) in enumerate(columns, start=1):
        _header_cell(ws, 1, col_idx, header, width)

    ws.row_dimensions[1].height = 30

    for row_idx, event in enumerate(events, start=2):
        fill = ALT_ROW_FILL if row_idx % 2 == 0 else PatternFill()
        for col_idx, (header, key, width) in enumerate(columns, start=1):
            value = event.get(key)
            if key == "severity":
                value = SEVERITY_LABELS.get(value, value)
            elif key == "status":
                value = STATUS_LABELS.get(value, value)
            elif key == "record_type":
                value = TYPE_LABELS.get(value, value)
            elif key == "repeat_issue":
                value = "Да" if value else "Нет"
            elif key == "requires_followup":
                value = "Да" if value else "Нет"

            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = NORMAL_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if fill.fill_type:
                cell.fill = fill

        ws.row_dimensions[row_idx].height = 30


INCIDENT_COLUMNS = [
    ("ID", "id", 6),
    ("Дата/Время", "event_datetime", 18),
    ("Заголовок", "title", 40),
    ("Канал", "channel", 15),
    ("Объект", "asset", 18),
    ("Критичность", "severity", 14),
    ("Статус", "status", 14),
    ("Причина", "root_cause", 30),
    ("Действия", "actions_taken", 35),
    ("Результат", "result", 25),
    ("Длительность (мин)", "duration_minutes", 10),
    ("Повторный", "repeat_issue", 10),
    ("Последействие", "requires_followup", 12),
    ("Ответственный", "reporter_name", 18),
]

WORK_COLUMNS = [
    ("ID", "id", 6),
    ("Дата/Время", "event_datetime", 18),
    ("Заголовок", "title", 40),
    ("Описание", "description", 40),
    ("Объект", "asset", 18),
    ("Канал", "channel", 15),
    ("Действия", "actions_taken", 35),
    ("Результат", "result", 25),
    ("Статус", "status", 14),
    ("Ответственный", "reporter_name", 18),
]

RISK_COLUMNS = [
    ("ID", "id", 6),
    ("Дата", "created_at", 18),
    ("Заголовок", "title", 40),
    ("Описание", "description", 40),
    ("Объект", "asset", 18),
    ("Канал", "channel", 15),
    ("Критичность", "severity", 14),
    ("Статус", "status", 14),
    ("Последействие", "requires_followup", 12),
    ("Заметка", "followup_note", 30),
]


def _build_kpi_sheet(wb: Workbook, kpi: dict) -> None:
    ws = wb.create_sheet("KPI")
    ws.sheet_view.showGridLines = False

    headers = ["Показатель", "Значение", "Оценка"]
    widths = [40, 15, 20]
    for col, (h, w) in enumerate(zip(headers, widths), 1):
        _header_cell(ws, 1, col, h, w)
    ws.row_dimensions[1].height = 28

    kpi_items = [
        ("Итоговый KPI отдела", kpi.get("department_kpi_score"), True),
        ("Оценка инцидентов (вес 40%)", kpi.get("incident_score"), True),
        ("Оценка устранения (вес 20%)", kpi.get("resolution_score"), True),
        ("Оценка работ (вес 20%)", kpi.get("work_completion_score"), True),
        ("Оценка повторных проблем (вес 10%)", kpi.get("repeat_issue_score"), True),
        ("Оценка AI-качества (вес 10%)", kpi.get("ai_quality_score"), True),
    ]

    sev_dist = kpi.get("severity_distribution", {}) or {}
    status_dist = kpi.get("status_distribution", {}) or {}

    for row_idx, (label, value, show_bar) in enumerate(kpi_items, start=2):
        ws.cell(row=row_idx, column=1, value=label).font = BOLD_FONT
        score_cell = ws.cell(row=row_idx, column=2, value=round(value, 1) if value is not None else "—")
        score_cell.fill = _kpi_score_fill(value)
        score_cell.font = Font(bold=True)
        score_cell.alignment = Alignment(horizontal="center")
        score_cell.border = THIN_BORDER

    row = len(kpi_items) + 3
    ws.cell(row=row, column=1, value="Распределение по критичности").font = BOLD_FONT
    row += 1
    for sev, count in sev_dist.items():
        ws.cell(row=row, column=1, value=SEVERITY_LABELS.get(sev, sev)).font = NORMAL_FONT
        ws.cell(row=row, column=2, value=count).alignment = Alignment(horizontal="center")
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Распределение по статусу").font = BOLD_FONT
    row += 1
    for st, count in status_dist.items():
        ws.cell(row=row, column=1, value=STATUS_LABELS.get(st, st)).font = NORMAL_FONT
        ws.cell(row=row, column=2, value=count).alignment = Alignment(horizontal="center")
        row += 1


def generate_excel_report(data: dict, output_path: str) -> str:
    """Generate a full Excel workbook and write to output_path."""
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    _build_dashboard_sheet(wb, data)

    events = data.get("events", {})

    _build_events_sheet(wb, "Инциденты", events.get("incidents", []), INCIDENT_COLUMNS)
    _build_events_sheet(wb, "Работы", events.get("works", []), WORK_COLUMNS)
    _build_events_sheet(wb, "Риски", events.get("risks", []), RISK_COLUMNS)
    _build_events_sheet(wb, "Оборудование", events.get("equipment", []), WORK_COLUMNS)
    _build_events_sheet(wb, "Заметки", events.get("notes", []), WORK_COLUMNS)
    _build_kpi_sheet(wb, data.get("kpi", {}))

    # AI summary sheet
    ws_ai = wb.create_sheet("AI Анализ")
    ai_text = data.get("ai_summary", "AI-анализ не сформирован")
    ws_ai.merge_cells("A1:D1")
    ws_ai["A1"].value = "AI-аналитическая сводка"
    ws_ai["A1"].font = Font(bold=True, size=14)
    ws_ai["A2"].value = ai_text
    ws_ai["A2"].alignment = Alignment(wrap_text=True)
    ws_ai.column_dimensions["A"].width = 120
    ws_ai.row_dimensions[2].height = max(60, len(ai_text) // 2)

    wb.save(output_path)
    return output_path
