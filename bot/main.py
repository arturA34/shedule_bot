import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings, setup_logging
from bot.handlers import all_routers
from database.db import init_db

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    logger.info("Initializing database...")
    await init_db()
    logger.info("Bot started")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Shutting down...")
    await bot.session.close()
    logger.info("Bot stopped")


async def main() -> None:
    setup_logging()
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    for router in all_routers:
        dp.include_router(router)

    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
