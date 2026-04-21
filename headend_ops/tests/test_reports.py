"""Tests for report generation (smoke tests)."""
import os
import tempfile
from datetime import date

import pytest

from app.reports.excel_exporter import generate_excel_report
from app.reports.pdf_exporter import generate_pdf_report


SAMPLE_REPORT_DATA = {
    "report_type": "monthly",
    "period_label": "Ежемесячный отчёт за Январь 2024",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "generated_at": "2024-02-01T09:00:00+00:00",
    "ai_summary": (
        "В январе 2024 года зафиксировано 5 инцидентов, из которых 2 критических. "
        "Среднее время устранения составило 45 минут. "
        "Выполнено 8 плановых работ. Рисков выявлено 2."
    ),
    "stats": {
        "total_events": 15,
        "total_incidents": 5,
        "total_works": 8,
        "total_risks": 2,
        "total_equipment": 0,
        "critical_incidents": 2,
        "resolved_incidents": 4,
        "unresolved_incidents": 1,
        "repeat_incidents": 1,
        "followups_open": 2,
        "kpi_score": 78.5,
        "avg_resolution_minutes": 45.0,
    },
    "kpi": {
        "department_kpi_score": 78.5,
        "incident_score": 72.0,
        "resolution_score": 80.0,
        "work_completion_score": 85.0,
        "repeat_issue_score": 88.0,
        "ai_quality_score": 70.0,
        "severity_distribution": {"critical": 2, "high": 2, "medium": 1},
        "status_distribution": {"resolved": 4, "new": 1},
        "top_channels": [{"channel_id": 1, "count": 3}],
        "top_assets": [{"asset_id": 1, "count": 2}],
    },
    "events": {
        "incidents": [
            {
                "id": 1,
                "record_type": "incident",
                "title": "Пропал звук на канале МИР",
                "description": "Потеря аудио с 14:20 до 14:32",
                "event_datetime": "2024-01-15T14:20:00",
                "end_datetime": "2024-01-15T14:32:00",
                "duration_minutes": 12,
                "channel": "МИР",
                "asset": "Encoder-2",
                "object_type": "channel",
                "severity": "high",
                "status": "resolved",
                "root_cause": "Сбой программного обеспечения кодировщика",
                "actions_taken": "Перезапуск сервиса encoder",
                "result": "Звук восстановлен",
                "requires_followup": False,
                "followup_note": None,
                "repeat_issue": False,
                "recurrence_count": 0,
                "reporter_name": "Иван Петров",
                "tags": ["encoder", "audio"],
                "ai_confidence": 0.91,
                "ai_score": 87,
                "created_at": "2024-01-15T14:22:00",
            },
            {
                "id": 2,
                "record_type": "incident",
                "title": "Повторный сбой transcoder-1",
                "description": "Зависание процесса транскодирования",
                "event_datetime": "2024-01-18T09:15:00",
                "end_datetime": None,
                "duration_minutes": 90,
                "channel": None,
                "asset": "Transcoder-1",
                "object_type": "equipment",
                "severity": "critical",
                "status": "resolved",
                "root_cause": "Утечка памяти в процессе",
                "actions_taken": "Перезапуск сервиса",
                "result": "Временно устранено",
                "requires_followup": True,
                "followup_note": "Требуется обновление ПО",
                "repeat_issue": True,
                "recurrence_count": 3,
                "reporter_name": "Анна Сидорова",
                "tags": ["transcoder", "memory"],
                "ai_confidence": 0.88,
                "ai_score": 72,
                "created_at": "2024-01-18T09:16:00",
            },
        ],
        "works": [
            {
                "id": 3,
                "record_type": "work",
                "title": "Плановое ТО mux-2",
                "description": "Выполнено плановое техническое обслуживание",
                "event_datetime": "2024-01-20T10:00:00",
                "end_datetime": "2024-01-20T12:00:00",
                "duration_minutes": 120,
                "channel": None,
                "asset": "Mux-2",
                "object_type": "equipment",
                "severity": None,
                "status": "resolved",
                "root_cause": None,
                "actions_taken": "Чистка, проверка, обновление прошивки",
                "result": "Оборудование в рабочем состоянии",
                "requires_followup": False,
                "followup_note": None,
                "repeat_issue": False,
                "recurrence_count": 0,
                "reporter_name": "Иван Петров",
                "tags": ["maintenance"],
                "ai_confidence": 0.95,
                "ai_score": 92,
                "created_at": "2024-01-20T10:05:00",
            }
        ],
        "risks": [
            {
                "id": 4,
                "record_type": "risk",
                "title": "Диск storage-1 заполнен на 92%",
                "description": "Высокая заполненность дискового массива",
                "event_datetime": "2024-01-22T15:00:00",
                "end_datetime": None,
                "duration_minutes": None,
                "channel": None,
                "asset": "Storage-1",
                "object_type": "server",
                "severity": "high",
                "status": "monitoring",
                "root_cause": "Недостаточная очистка архивных данных",
                "actions_taken": "Мониторинг",
                "result": None,
                "requires_followup": True,
                "followup_note": "Необходимо очистить архив",
                "repeat_issue": False,
                "recurrence_count": 0,
                "reporter_name": "Анна Сидорова",
                "tags": ["storage", "disk"],
                "ai_confidence": 0.89,
                "ai_score": 80,
                "created_at": "2024-01-22T15:01:00",
            }
        ],
        "equipment": [],
        "notes": [],
    },
}


class TestExcelExporter:
    def test_excel_report_generated(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = f.name
        try:
            result = generate_excel_report(SAMPLE_REPORT_DATA, path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 1000  # must have content
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_excel_report_with_empty_events(self):
        empty_data = {**SAMPLE_REPORT_DATA, "events": {
            "incidents": [], "works": [], "risks": [], "equipment": [], "notes": []
        }}
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = f.name
        try:
            result = generate_excel_report(empty_data, path)
            assert os.path.exists(result)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestPDFExporter:
    def test_pdf_report_generated(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = generate_pdf_report(SAMPLE_REPORT_DATA, path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 1000  # must have content
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_pdf_report_no_crash_on_empty(self):
        empty_data = {**SAMPLE_REPORT_DATA, "events": {
            "incidents": [], "works": [], "risks": [], "equipment": [], "notes": []
        }, "ai_summary": None}
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = generate_pdf_report(empty_data, path)
            assert os.path.exists(result)
        finally:
            if os.path.exists(path):
                os.unlink(path)
