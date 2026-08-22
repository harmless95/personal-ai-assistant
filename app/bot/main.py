import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.client import AssistantApiClient
from app.bot.handlers import build_root_router
from app.bot.sessions import SessionStore
from app.config import settings

logger = logging.getLogger(__name__)


async def _run() -> None:
    token = settings.telegram.bot_token.get_secret_value().strip()
    if not token:
        raise RuntimeError("TELEGRAM__BOT_TOKEN is empty. Set it in .env before starting the bot.")

    api = AssistantApiClient(
        base_url=settings.telegram.api_base_url,
        api_prefix=settings.api_prefix_v1,
    )
    sessions = SessionStore()
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_root_router())

    logger.info("telegram_bot_starting api_base_url=%s", settings.telegram.api_base_url)
    try:
        await dispatcher.start_polling(bot, api=api, sessions=sessions)
    finally:
        await api.aclose()
        await bot.session.close()


def run_bot() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())
