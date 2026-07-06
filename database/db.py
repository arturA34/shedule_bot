import json
import logging
from typing import Optional

import asyncpg

from bot.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(dsn=settings.db_dsn)
    return _pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")


async def get_connection() -> asyncpg.Connection:
    settings = get_settings()
    return await asyncpg.connect(settings.db_dsn)


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                primary_group TEXT NOT NULL,
                subgroups JSONB
            );

            CREATE TABLE IF NOT EXISTS schedule (
                id SERIAL PRIMARY KEY,
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

            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                fio VARCHAR(255) NOT NULL,
                department VARCHAR(255),
                email VARCHAR(255)
            );

            CREATE INDEX IF NOT EXISTS idx_schedule_group_name
                ON schedule(group_name);
            CREATE INDEX IF NOT EXISTS idx_schedule_date
                ON schedule(date);
        """)
        
        # Check if teachers table is empty and seed if needed
        count = await conn.fetchval("SELECT COUNT(*) FROM teachers")
        if count == 0:
            await conn.executemany(
                """
                INSERT INTO teachers (fio, department, email)
                VALUES ($1, $2, $3)
                """,
                [
                    ("Иванов И.И.", "Кафедра Высшей Математики", "ivanov.ii@university.edu"),
                    ("Петров П.П.", "Кафедра Информационных Технологий", "petrov.pp@university.edu"),
                    ("Сидоров С.С.", "Кафедра Общей Физики", "sidorov.ss@university.edu"),
                    ("Козлова А.В.", "Кафедра Истории", "kozlova.av@university.edu"),
                    ("Новикова Е.Д.", "Кафедра Философии", "novikova.ed@university.edu"),
                    ("Смирнова О.Л.", "Кафедра Иностранных Языков", "smirnova.ol@university.edu"),
                    ("Козлов В.Н.", "Кафедра Физического Воспитания", "kozlov.vn@university.edu"),
                ]
            )
            logger.info("Teachers table seeded with default records.")
    logger.info("Database schema initialized.")


async def get_user(telegram_id: int) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT telegram_id, primary_group, subgroups FROM users WHERE telegram_id = $1",
        telegram_id,
    )
    if row is None:
        return None

    subgroups_val = row["subgroups"]
    if isinstance(subgroups_val, str):
        subgroups = json.loads(subgroups_val)
    elif subgroups_val is None:
        subgroups = []
    else:
        subgroups = subgroups_val

    return {
        "telegram_id": row["telegram_id"],
        "primary_group": row["primary_group"],
        "subgroups": subgroups,
    }


async def create_user(telegram_id: int, primary_group: str, subgroups: list[dict]) -> None:
    pool = await get_pool()
    subgroups_json = json.dumps(subgroups, ensure_ascii=False)
    await pool.execute(
        """
        INSERT INTO users (telegram_id, primary_group, subgroups)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (telegram_id) DO UPDATE
        SET primary_group = EXCLUDED.primary_group,
            subgroups = EXCLUDED.subgroups
        """,
        telegram_id,
        primary_group,
        subgroups_json,
    )


async def update_user(telegram_id: int, primary_group: str, subgroups: list[dict]) -> None:
    pool = await get_pool()
    subgroups_json = json.dumps(subgroups, ensure_ascii=False)
    await pool.execute(
        "UPDATE users SET primary_group = $1, subgroups = $2::jsonb WHERE telegram_id = $3",
        primary_group,
        subgroups_json,
        telegram_id,
    )


async def get_all_groups() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT group_name FROM schedule ORDER BY group_name")
    return [row["group_name"] for row in rows]


async def get_lessons_by_group_and_date(group_name: str, date_str: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name
        FROM schedule
        WHERE group_name = $1 AND date = $2
        ORDER BY lesson_number
        """,
        group_name,
        date_str,
    )
    return [dict(row) for row in rows]


async def get_lesson_by_id(lesson_id: int) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name FROM schedule WHERE id = $1
        """,
        lesson_id,
    )
    return dict(row) if row else None


async def create_lesson(
    day_of_week: str,
    date_str: str,
    lesson_number: int,
    start_time: str,
    end_time: str,
    subject: str,
    teacher: str,
    room: str,
    building: str,
    lesson_type: str,
    group_name: str,
    subgroup_name: Optional[str]
) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO schedule
            (day_of_week, date, lesson_number, start_time, end_time,
             subject, teacher, room, building, lesson_type,
             group_name, subgroup_name)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
        day_of_week,
        date_str,
        lesson_number,
        start_time,
        end_time,
        subject,
        teacher,
        room,
        building,
        lesson_type,
        group_name,
        subgroup_name,
    )


async def update_lesson_subject(lesson_id: int, subject: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET subject = $1 WHERE id = $2",
        subject,
        lesson_id,
    )


async def update_lesson_room_building(lesson_id: int, room: str, building: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET room = $1, building = $2 WHERE id = $3",
        room,
        building,
        lesson_id,
    )


async def update_lesson_teacher(lesson_id: int, teacher: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET teacher = $1 WHERE id = $2",
        teacher,
        lesson_id,
    )


async def delete_lesson(lesson_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM schedule WHERE id = $1",
        lesson_id,
    )


async def search_teachers(query: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, fio, department, email FROM teachers WHERE fio ILIKE $1 ORDER BY fio",
        f"%{query}%",
    )
    return [dict(row) for row in rows]


async def get_teacher_by_id(teacher_id: int) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, fio, department, email FROM teachers WHERE id = $1",
        teacher_id,
    )
    return dict(row) if row else None


async def get_lessons_by_teacher_and_date(teacher_fio: str, date_str: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name
        FROM schedule
        WHERE teacher = $1 AND date = $2
        ORDER BY lesson_number
        """,
        teacher_fio,
        date_str,
    )
    return [dict(row) for row in rows]


async def get_lessons_by_teacher_and_date_range(
    teacher_fio: str, start_date_str: str, end_date_str: str
) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name
        FROM schedule
        WHERE teacher = $1 AND date BETWEEN $2 AND $3
        ORDER BY date, lesson_number
        """,
        teacher_fio,
        start_date_str,
        end_date_str,
    )
    return [dict(row) for row in rows]



