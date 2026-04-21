"""Telegram bot entry point using aiogram 3.x."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import BotCommand, ErrorEvent

from app.bot.handlers import commands, messages
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """Register bot command descriptions (shown in Telegram command menu)."""
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="incident", description="Зафиксировать инцидент"),
        BotCommand(command="work", description="Зафиксировать работу"),
        BotCommand(command="risk", description="Зафиксировать риск"),
        BotCommand(command="equipment", description="Состояние оборудования"),
        BotCommand(command="note", description="Добавить заметку"),
        BotCommand(command="report_day", description="Ежедневный отчёт"),
        BotCommand(command="report_week", description="Еженедельный отчёт"),
        BotCommand(command="report_month", description="Ежемесячный отчёт"),
        BotCommand(command="kpi", description="Текущие KPI"),
        BotCommand(command="channels", description="Список каналов"),
        BotCommand(command="assets", description="Список оборудования"),
        BotCommand(command="pending_review", description="Записи на проверке"),
    ])


async def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("telegram_token_not_set")
        return

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(commands.router)
    dp.include_router(messages.router)

    await set_bot_commands(bot)
    logger.info("bot_starting", mode=settings.TELEGRAM_MODE)

    if settings.TELEGRAM_MODE == "webhook":
        # Webhook mode for production
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        from aiohttp import web

        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
        )
        logger.info("webhook_set", url=webhook_url)

        # Webhook server runs alongside — for simple MVP we just use polling
        await dp.start_polling(bot)
    else:
        # Polling mode for development
        logger.info("bot_polling_started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
