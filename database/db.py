import aiosqlite

from bot.config import get_settings


async def get_connection() -> aiosqlite.Connection:
    settings = get_settings()
    conn = await aiosqlite.connect(settings.DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db() -> None:
    conn = await get_connection()
    try:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                primary_group TEXT NOT NULL,
                subgroups TEXT
            );

            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week TEXT,
                date TEXT,
                lesson_number INTEGER,
                start_time TEXT,
                end_time TEXT,
                subject TEXT,
                teacher TEXT,
                room TEXT,
                building TEXT,
                lesson_type TEXT,
                group_name TEXT,
                subgroup_name TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_schedule_group_name
                ON schedule(group_name);
            CREATE INDEX IF NOT EXISTS idx_schedule_date
                ON schedule(date);
        """)
        await conn.commit()
    finally:
        await conn.close()
