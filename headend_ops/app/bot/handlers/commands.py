"""Bot command handlers — all Russian UI."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

import httpx

from app.bot import texts
from app.core.config import settings
from app.core.logging import get_logger

router = Router()
logger = get_logger(__name__)

API_BASE = f"http://{settings.API_HOST if settings.API_HOST != '0.0.0.0' else 'localhost'}:{settings.API_PORT}{settings.API_PREFIX}"


async def _api_get(path: str) -> dict | list | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{API_BASE}{path}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("api_call_failed", path=path, error=str(e))
        return None


async def _api_post(path: str, json_data: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{API_BASE}{path}", json=json_data)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("api_post_failed", path=path, error=str(e))
        return None


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(texts.WELCOME, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP, parse_mode="HTML")


@router.message(Command("incident"))
async def cmd_incident(message: Message) -> None:
    await message.answer(texts.INCIDENT_PROMPT, parse_mode="HTML")


@router.message(Command("work"))
async def cmd_work(message: Message) -> None:
    await message.answer(texts.WORK_PROMPT, parse_mode="HTML")


@router.message(Command("risk"))
async def cmd_risk(message: Message) -> None:
    await message.answer(texts.RISK_PROMPT, parse_mode="HTML")


@router.message(Command("equipment"))
async def cmd_equipment(message: Message) -> None:
    await message.answer(texts.EQUIPMENT_PROMPT, parse_mode="HTML")


@router.message(Command("note"))
async def cmd_note(message: Message) -> None:
    await message.answer(texts.NOTE_PROMPT, parse_mode="HTML")


@router.message(Command("kpi"))
async def cmd_kpi(message: Message) -> None:
    data = await _api_get("/dashboard/summary")
    if data:
        monthly = data.get("monthly", {})
        await message.answer(texts.kpi_message(monthly), parse_mode="HTML")
    else:
        await message.answer("❌ Не удалось получить данные KPI. Попробуйте позже.")


@router.message(Command("channels"))
async def cmd_channels(message: Message) -> None:
    channels = await _api_get("/dictionaries/channels")
    if not channels:
        await message.answer("❌ Не удалось получить список каналов.")
        return
    lines = [texts.CHANNELS_HEADER]
    for ch in channels[:30]:
        lines.append(f"• <b>{ch['code']}</b> — {ch['name']}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("assets"))
async def cmd_assets(message: Message) -> None:
    assets = await _api_get("/dictionaries/assets")
    if not assets:
        await message.answer("❌ Не удалось получить список оборудования.")
        return
    lines = [texts.ASSETS_HEADER]
    for a in assets[:30]:
        lines.append(f"• <b>{a['code']}</b> — {a['name']} [{a['asset_type']}]")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("pending_review"))
async def cmd_pending_review(message: Message) -> None:
    reviews = await _api_get("/review/pending")
    if reviews is None:
        await message.answer("❌ Не удалось получить список.")
        return
    await message.answer(texts.pending_reviews_message(reviews), parse_mode="HTML")


@router.message(Command("report_day"))
async def cmd_report_day(message: Message) -> None:
    await message.answer(texts.REPORT_GENERATING)
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    result = await _api_post(
        "/reports/generate",
        {"report_type": "daily", "period_start": today, "generate_excel": True, "generate_pdf": True},
    )
    if result and result.get("status") == "completed":
        summary = result.get("executive_summary", "")
        text = f"✅ <b>Ежедневный отчёт сформирован</b>\n\n"
        if summary:
            text += f"{summary[:500]}\n\n"
        text += f"ID отчёта: #{result.get('id')}\nСкачать: /api/v1/reports/{result.get('id')}/download/excel"
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer(texts.REPORT_FAILED)


@router.message(Command("report_week"))
async def cmd_report_week(message: Message) -> None:
    await message.answer(texts.REPORT_GENERATING)
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    result = await _api_post(
        "/reports/generate",
        {"report_type": "weekly", "period_start": today},
    )
    if result and result.get("status") == "completed":
        await message.answer(
            f"✅ <b>Еженедельный отчёт сформирован</b>\nID: #{result.get('id')}",
            parse_mode="HTML",
        )
    else:
        await message.answer(texts.REPORT_FAILED)


@router.message(Command("report_month"))
async def cmd_report_month(message: Message) -> None:
    await message.answer(texts.REPORT_GENERATING)
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    result = await _api_post(
        "/reports/generate",
        {"report_type": "monthly", "period_start": today},
    )
    if result and result.get("status") == "completed":
        summary = result.get("executive_summary", "")
        text = f"✅ <b>Ежемесячный отчёт сформирован</b>\n\n"
        if summary:
            text += f"{summary[:800]}\n\n"
        kpi = result.get("kpi_data", {}) or {}
        score = kpi.get("department_kpi_score")
        if score:
            text += f"📊 KPI отдела: <b>{score:.1f}/100</b>"
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer(texts.REPORT_FAILED)
