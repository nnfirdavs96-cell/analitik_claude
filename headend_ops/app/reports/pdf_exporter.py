"""PDF report exporter using ReportLab."""
from datetime import datetime
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register DejaVu font for Unicode/Cyrillic support
import os

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "fonts")

def _register_fonts() -> str:
    """Register Cyrillic-capable font. Returns font name."""
    dejavu_path = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    dejavu_bold_path = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

    try:
        if os.path.exists(dejavu_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans", dejavu_path))
        if os.path.exists(dejavu_bold_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", dejavu_bold_path))
        return "DejaVuSans"
    except Exception:
        return "Helvetica"


FONT_NAME = _register_fonts()
FONT_BOLD = f"{FONT_NAME}-Bold" if FONT_NAME == "DejaVuSans" else "Helvetica-Bold"

DARK_BLUE = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#2E75B6")
LIGHT_BLUE = colors.HexColor("#D6E4F0")
RED = colors.HexColor("#FF0000")
GREEN = colors.HexColor("#00AA00")
ORANGE = colors.HexColor("#FFA500")

SEVERITY_LABELS = {"critical": "Критическая", "high": "Высокая", "medium": "Средняя", "low": "Низкая"}
STATUS_LABELS = {
    "new": "Новый", "in_progress": "В работе", "resolved": "Устранено",
    "monitoring": "Мониторинг", "closed": "Закрыто",
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", fontName=FONT_BOLD, fontSize=20, textColor=DARK_BLUE,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=FONT_NAME, fontSize=12, textColor=BLUE,
            alignment=TA_CENTER, spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "section", fontName=FONT_BOLD, fontSize=13, textColor=DARK_BLUE,
            spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", fontName=FONT_NAME, fontSize=10, leading=14,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small", fontName=FONT_NAME, fontSize=8, textColor=colors.grey,
        ),
        "kpi_good": ParagraphStyle(
            "kpi_good", fontName=FONT_BOLD, fontSize=11, textColor=GREEN, alignment=TA_CENTER
        ),
        "kpi_bad": ParagraphStyle(
            "kpi_bad", fontName=FONT_BOLD, fontSize=11, textColor=RED, alignment=TA_CENTER
        ),
    }


def _kpi_color(score: Optional[float]) -> colors.Color:
    if score is None:
        return colors.grey
    if score >= 75:
        return GREEN
    if score >= 50:
        return ORANGE
    return RED


def _build_kpi_table(kpi: dict, styles: dict) -> Table:
    kpi_items = [
        ("Итоговый KPI отдела", kpi.get("department_kpi_score")),
        ("Оценка инцидентов (40%)", kpi.get("incident_score")),
        ("Оценка устранения (20%)", kpi.get("resolution_score")),
        ("Оценка работ (20%)", kpi.get("work_completion_score")),
        ("Повторные проблемы (10%)", kpi.get("repeat_issue_score")),
        ("AI-качество (10%)", kpi.get("ai_quality_score")),
    ]

    rows = [[
        Paragraph("Показатель KPI", ParagraphStyle("h", fontName=FONT_BOLD, fontSize=10, textColor=colors.white)),
        Paragraph("Значение", ParagraphStyle("h", fontName=FONT_BOLD, fontSize=10, textColor=colors.white, alignment=TA_CENTER)),
    ]]
    for label, value in kpi_items:
        val_str = f"{round(value, 1)}" if value is not None else "—"
        val_color = _kpi_color(value)
        rows.append([
            Paragraph(label, styles["body"]),
            Paragraph(val_str, ParagraphStyle("v", fontName=FONT_BOLD, fontSize=11,
                                              textColor=val_color, alignment=TA_CENTER)),
        ])

    table = Table(rows, colWidths=[12 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _build_incident_table(incidents: list[dict], styles: dict) -> Optional[Table]:
    if not incidents:
        return None

    headers = ["#", "Дата", "Заголовок", "Канал", "Объект", "Критичность", "Статус", "Мин"]
    rows = [
        [Paragraph(h, ParagraphStyle("h", fontName=FONT_BOLD, fontSize=8, textColor=colors.white))
         for h in headers]
    ]
    for i, ev in enumerate(incidents[:50], 1):  # limit to 50 per PDF
        sev = SEVERITY_LABELS.get(ev.get("severity", ""), ev.get("severity", "—") or "—")
        st = STATUS_LABELS.get(ev.get("status", ""), ev.get("status", "—") or "—")
        dt = ev.get("event_datetime", ev.get("created_at", ""))[:10] if ev.get("event_datetime") or ev.get("created_at") else "—"
        rows.append([
            str(i),
            dt,
            Paragraph((ev.get("title") or "")[:60], ParagraphStyle("t", fontName=FONT_NAME, fontSize=8)),
            (ev.get("channel") or "—")[:15],
            (ev.get("asset") or "—")[:15],
            sev,
            st,
            str(ev.get("duration_minutes") or "—"),
        ])

    col_widths = [0.8*cm, 2.2*cm, 6*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.2*cm, 1.3*cm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def generate_pdf_report(data: dict, output_path: str) -> str:
    """Generate PDF management report and write to output_path."""
    styles = _styles()
    story = []

    # Title page
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(data.get("period_label", "Оперативный отчёт"), styles["title"]))
    story.append(Paragraph(
        f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE))
    story.append(Spacer(1, 0.5 * cm))

    stats = data.get("stats", {})
    kpi = data.get("kpi", {})
    events = data.get("events", {})

    # Executive summary
    ai_text = data.get("ai_summary")
    if ai_text:
        story.append(Paragraph("Аналитическая сводка", styles["section"]))
        for para in ai_text.split("\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), styles["body"]))
        story.append(Spacer(1, 0.4 * cm))

    # Stats overview
    story.append(Paragraph("Статистика периода", styles["section"]))
    stat_data = [
        ["Показатель", "Значение"],
        ["Всего записей", str(stats.get("total_events", 0))],
        ["Инцидентов", str(stats.get("total_incidents", 0))],
        ["Критических инцидентов", str(stats.get("critical_incidents", 0))],
        ["Устранено", str(stats.get("resolved_incidents", 0))],
        ["Не устранено", str(stats.get("unresolved_incidents", 0))],
        ["Повторных", str(stats.get("repeat_incidents", 0))],
        ["Работ", str(stats.get("total_works", 0))],
        ["Рисков", str(stats.get("total_risks", 0))],
        ["Среднее время устранения (мин)", str(stats.get("avg_resolution_minutes") or "—")],
    ]
    stat_table = Table(stat_data, colWidths=[10 * cm, 4 * cm])
    stat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 0.5 * cm))

    # KPI
    story.append(Paragraph("KPI отдела", styles["section"]))
    story.append(_build_kpi_table(kpi, styles))
    story.append(Spacer(1, 0.5 * cm))

    # Incidents table
    incidents = events.get("incidents", [])
    if incidents:
        story.append(PageBreak())
        story.append(Paragraph(f"Инциденты ({len(incidents)})", styles["section"]))
        inc_table = _build_incident_table(incidents, styles)
        if inc_table:
            story.append(inc_table)

    # Risks
    risks = events.get("risks", [])
    if risks:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"Риски ({len(risks)})", styles["section"]))
        for risk in risks[:20]:
            line = f"• {risk.get('title', '')} — {risk.get('description', '')[:150]}"
            story.append(Paragraph(line, styles["body"]))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "Headend Operations Platform — автоматически сформированный отчёт",
        styles["small"],
    ))

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=data.get("period_label", "Отчёт"),
        author="Headend Ops",
    )
    doc.build(story)
    return output_path
