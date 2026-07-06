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
    max_retries = 5
    retry_delay = 3
    for attempt in range(1, max_retries + 1):
        try:
            await init_db()
            logger.info("Database initialized successfully.")
            break
        except Exception as e:
            logger.warning(
                f"Database initialization failed (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {retry_delay} seconds..."
            )
            if attempt == max_retries:
                logger.error("Could not connect to the database. Exiting...")
                raise e
            await asyncio.sleep(retry_delay)
    logger.info("Bot started")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Shutting down...")
    from database.db import close_db
    await close_db()
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
