import asyncio
import sys
import uuid
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path, чтобы импортировать модули bot и database
sys.path.append(str(Path(__file__).parent.parent))

from bot.config import get_settings
from database.db import add_admin_invite, close_db, init_db


async def generate() -> None:
    # Инициализируем БД и создаем таблицы, если их нет
    await init_db()

    settings = get_settings()
    bot_username = settings.BOT_USERNAME.strip()
    if not bot_username:
        print("Ошибка: BOT_USERNAME не задан в .env", file=sys.stderr)
        await close_db()
        sys.exit(1)

    token = str(uuid.uuid4())

    try:
        await add_admin_invite(token)
        link = f"https://t.me/{bot_username}?start=admin_{token}"
        print("Токен приглашения успешно создан!")
        print(f"Ссылка для регистрации администратора:\n{link}")
    except Exception as e:
        print(f"Ошибка при сохранении токена в БД: {e}", file=sys.stderr)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(generate())
