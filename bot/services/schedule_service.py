import datetime
import json
from typing import Optional

import aiosqlite

from bot.config import get_settings


class UserNotRegisteredError(Exception):
    """Пользователь не найден в таблице users."""


async def _get_connection() -> aiosqlite.Connection:
    settings = get_settings()
    conn = await aiosqlite.connect(settings.DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def _get_user_profile(telegram_id: int) -> Optional[dict]:
    conn = await _get_connection()
    try:
        cursor = await conn.execute(
            "SELECT primary_group, subgroups FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "primary_group": row["primary_group"],
            "subgroups": json.loads(row["subgroups"]) if row["subgroups"] else [],
        }
    finally:
        await conn.close()


def _matches_subgroup(lesson_subject: str, lesson_subgroup: Optional[str], user_subgroups: list[dict]) -> bool:
    """Проверяет, подходит ли занятие пользователю по подгруппе.

    - Если у занятия нет подгруппы — занятие общее, подходит всем.
    - Если подгруппа есть — она должна совпадать с подгруппой пользователя
      по этому предмету.
    """
    if not lesson_subgroup:
        return True

    user_sub_map = {s["subject"]: s["subgroup"] for s in user_subgroups}
    return user_sub_map.get(lesson_subject) == lesson_subgroup


async def get_user_schedule(telegram_id: int, target_date: datetime.date) -> list[dict]:
    """Возвращает список занятий пользователя на указанную дату."""
    profile = await _get_user_profile(telegram_id)
    if profile is None:
        raise UserNotRegisteredError(
            f"Пользователь с telegram_id={telegram_id} не зарегистрирован."
        )

    conn = await _get_connection()
    try:
        date_str = target_date.isoformat()
        cursor = await conn.execute(
            """
            SELECT id, day_of_week, date, lesson_number, start_time, end_time,
                   subject, teacher, room, building, lesson_type,
                   group_name, subgroup_name
            FROM schedule
            WHERE group_name = ? AND date = ?
            ORDER BY lesson_number
            """,
            (profile["primary_group"], date_str),
        )
        rows = await cursor.fetchall()

        result = []
        for row in rows:
            if not _matches_subgroup(row["subject"], row["subgroup_name"], profile["subgroups"]):
                continue
            result.append({
                "id": row["id"],
                "day_of_week": row["day_of_week"],
                "date": row["date"],
                "lesson_number": row["lesson_number"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "subject": row["subject"],
                "teacher": row["teacher"],
                "room": row["room"],
                "building": row["building"],
                "lesson_type": row["lesson_type"],
                "group_name": row["group_name"],
                "subgroup_name": row["subgroup_name"],
            })
        return result
    finally:
        await conn.close()


async def get_user_schedule_range(
    telegram_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> dict[str, list[dict]]:
    """Возвращает расписание пользователя на диапазон дат.

    Returns:
        Словарь {дата (iso): список занятий}.
    """
    profile = await _get_user_profile(telegram_id)
    if profile is None:
        raise UserNotRegisteredError(
            f"Пользователь с telegram_id={telegram_id} не зарегистрирован."
        )

    conn = await _get_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT id, day_of_week, date, lesson_number, start_time, end_time,
                   subject, teacher, room, building, lesson_type,
                   group_name, subgroup_name
            FROM schedule
            WHERE group_name = ? AND date BETWEEN ? AND ?
            ORDER BY date, lesson_number
            """,
            (profile["primary_group"], start_date.isoformat(), end_date.isoformat()),
        )
        rows = await cursor.fetchall()

        result: dict[str, list[dict]] = {}
        for row in rows:
            if not _matches_subgroup(row["subject"], row["subgroup_name"], profile["subgroups"]):
                continue
            entry = {
                "id": row["id"],
                "day_of_week": row["day_of_week"],
                "date": row["date"],
                "lesson_number": row["lesson_number"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "subject": row["subject"],
                "teacher": row["teacher"],
                "room": row["room"],
                "building": row["building"],
                "lesson_type": row["lesson_type"],
                "group_name": row["group_name"],
                "subgroup_name": row["subgroup_name"],
            }
            result.setdefault(row["date"], []).append(entry)
        return result
    finally:
        await conn.close()
