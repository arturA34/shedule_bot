import json
from typing import Optional

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


async def get_user(telegram_id: int) -> Optional[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            "SELECT telegram_id, primary_group, subgroups FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "telegram_id": row["telegram_id"],
            "primary_group": row["primary_group"],
            "subgroups": json.loads(row["subgroups"]) if row["subgroups"] else [],
        }
    finally:
        await conn.close()


async def create_user(telegram_id: int, primary_group: str, subgroups: list[dict]) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT OR REPLACE INTO users (telegram_id, primary_group, subgroups) VALUES (?, ?, ?)",
            (telegram_id, primary_group, json.dumps(subgroups, ensure_ascii=False)),
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_user(telegram_id: int, primary_group: str, subgroups: list[dict]) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE users SET primary_group = ?, subgroups = ? WHERE telegram_id = ?",
            (primary_group, json.dumps(subgroups, ensure_ascii=False), telegram_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_all_groups() -> list[str]:
    conn = await get_connection()
    try:
        cursor = await conn.execute("SELECT DISTINCT group_name FROM schedule ORDER BY group_name")
        rows = await cursor.fetchall()
        return [row["group_name"] for row in rows]
    finally:
        await conn.close()


async def get_lessons_by_group_and_date(group_name: str, date_str: str) -> list[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT id, day_of_week, date, lesson_number, start_time, end_time,
                   subject, teacher, room, building, lesson_type,
                   group_name, subgroup_name
            FROM schedule
            WHERE group_name = ? AND date = ?
            ORDER BY lesson_number
            """,
            (group_name, date_str),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_lesson_by_id(lesson_id: int) -> Optional[dict]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT id, day_of_week, date, lesson_number, start_time, end_time,
                   subject, teacher, room, building, lesson_type,
                   group_name, subgroup_name FROM schedule WHERE id = ?
            """,
            (lesson_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


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
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO schedule
                (day_of_week, date, lesson_number, start_time, end_time,
                 subject, teacher, room, building, lesson_type,
                 group_name, subgroup_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (day_of_week, date_str, lesson_number, start_time, end_time,
             subject, teacher, room, building, lesson_type,
             group_name, subgroup_name),
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_lesson_subject(lesson_id: int, subject: str) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE schedule SET subject = ? WHERE id = ?",
            (subject, lesson_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_lesson_room_building(lesson_id: int, room: str, building: str) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE schedule SET room = ?, building = ? WHERE id = ?",
            (room, building, lesson_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_lesson_teacher(lesson_id: int, teacher: str) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "UPDATE schedule SET teacher = ? WHERE id = ?",
            (teacher, lesson_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def delete_lesson(lesson_id: int) -> None:
    conn = await get_connection()
    try:
        await conn.execute(
            "DELETE FROM schedule WHERE id = ?",
            (lesson_id,),
        )
        await conn.commit()
    finally:
        await conn.close()


