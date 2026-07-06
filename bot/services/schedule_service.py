import datetime
import json
from typing import Optional

from bot.config import get_settings
from database.db import get_pool


class UserNotRegisteredError(Exception):
    """Пользователь не найден в таблице users."""


async def _get_user_profile(telegram_id: int) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT primary_group, subgroups FROM users WHERE telegram_id = $1",
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
        "primary_group": row["primary_group"],
        "subgroups": subgroups,
    }


def _matches_subgroup(lesson_subject: str, lesson_subgroup: Optional[str], user_subgroups: list[dict]) -> bool:
    """Проверяет, подходит ли занятие пользователю по подгруппе.

    - Если у занятия нет подгруппы — занятие общее, подходит всем.
    - Если подгруппа есть — она должна совпадать с подгруппой пользователя
      по этому предмету. Если пользователь не настроил подгруппу для этого
      предмета, занятие также показывается.
    """
    if not lesson_subgroup:
        return True

    user_sub_map = {s["subject"]: s["subgroup"] for s in user_subgroups}
    if lesson_subject not in user_sub_map:
        return True
    return user_sub_map.get(lesson_subject) == lesson_subgroup


async def has_schedule_data_for_date(target_date: datetime.date) -> bool:
    """Проверяет, есть ли вообще записи в schedule на указанную дату."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT 1 FROM schedule WHERE date = $1 LIMIT 1",
        target_date.isoformat(),
    )
    return row is not None


async def get_user_schedule(telegram_id: int, target_date: datetime.date) -> list[dict]:
    """Возвращает список занятий пользователя на указанную дату."""
    profile = await _get_user_profile(telegram_id)
    if profile is None:
        raise UserNotRegisteredError(
            f"Пользователь с telegram_id={telegram_id} не зарегистрирован."
        )

    pool = await get_pool()
    date_str = target_date.isoformat()
    rows = await pool.fetch(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name
        FROM schedule
        WHERE group_name = $1 AND date = $2
        ORDER BY lesson_number
        """,
        profile["primary_group"],
        date_str,
    )

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

    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, day_of_week, date, lesson_number, start_time, end_time,
               subject, teacher, room, building, lesson_type,
               group_name, subgroup_name
        FROM schedule
        WHERE group_name = $1 AND date BETWEEN $2 AND $3
        ORDER BY date, lesson_number
        """,
        profile["primary_group"],
        start_date.isoformat(),
        end_date.isoformat(),
    )

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
