import datetime
import json
from typing import Any, Optional

import aiosqlite
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings


def detect_schedule_changes(old_lessons: list[dict[str, Any]], new_lessons: list[dict[str, Any]]) -> dict[str, list]:
    """Сравнивает два набора занятий и возвращает разницу."""
    old_map = {
        (l["group_name"], l["date"], l["lesson_number"], l.get("subgroup_name")): l
        for l in old_lessons
    }
    new_map = {
        (l["group_name"], l["date"], l["lesson_number"], l.get("subgroup_name")): l
        for l in new_lessons
    }

    added = []
    deleted = []
    changed = []

    # Находим удаленные
    for key, old_lesson in old_map.items():
        if key not in new_map:
            deleted.append(old_lesson)

    # Находим добавленные и измененные
    for key, new_lesson in new_map.items():
        if key not in old_map:
            added.append(new_lesson)
        else:
            old_lesson = old_map[key]
            diff_fields = {}
            for field in ["subject", "teacher", "room", "building", "lesson_type", "start_time", "end_time"]:
                if old_lesson.get(field) != new_lesson.get(field):
                    diff_fields[field] = (old_lesson.get(field), new_lesson.get(field))
            if diff_fields:
                changed.append({
                    "old": old_lesson,
                    "new": new_lesson,
                    "diff": diff_fields,
                })

    return {
        "added": added,
        "deleted": deleted,
        "changed": changed,
    }


async def get_all_users() -> list[dict[str, Any]]:
    """Возвращает всех зарегистрированных пользователей из БД."""
    settings = get_settings()
    async with aiosqlite.connect(settings.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT telegram_id, primary_group, subgroups FROM users")
        rows = await cursor.fetchall()
        users = []
        for row in rows:
            users.append({
                "telegram_id": row["telegram_id"],
                "primary_group": row["primary_group"],
                "subgroups": json.loads(row["subgroups"]) if row["subgroups"] else [],
            })
        return users


def get_user_changes(user: dict[str, Any], changes: dict[str, list]) -> dict[str, list]:
    """Фильтрует изменения, оставляя только те, которые затрагивают конкретного пользователя."""
    user_group = user["primary_group"]
    user_subgroups = user["subgroups"]

    def matches_user(lesson: dict[str, Any]) -> bool:
        if lesson["group_name"] != user_group:
            return False
        # Проверяем подгруппу
        subgrp = lesson.get("subgroup_name")
        if not subgrp:
            return True
        subject = lesson["subject"]
        user_sub_map = {s["subject"]: s["subgroup"] for s in user_subgroups}
        return user_sub_map.get(subject) == subgrp

    user_added = [l for l in changes["added"] if matches_user(l)]
    user_deleted = [l for l in changes["deleted"] if matches_user(l)]
    user_changed = [c for c in changes["changed"] if matches_user(c["new"])]

    return {
        "added": user_added,
        "deleted": user_deleted,
        "changed": user_changed,
    }


def format_date(date_str: str) -> str:
    """Форматирует строку даты YYYY-MM-DD в DD.MM (День_недели)."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        wd_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        return f"{dt.strftime('%d.%m')} ({wd_ru[dt.weekday()]})"
    except Exception:
        return date_str


def format_notification(changes: dict[str, list]) -> str:
    """Сборка красивого сводного сообщения об изменениях в расписании."""
    lines = ["🔔 <b>Внимание! Обнаружены изменения в вашем расписании:</b>\n"]

    if changes["added"]:
        lines.append("<b>➕ Новые занятия:</b>")
        for l in changes["added"]:
            sub = f" (Подгруппа {l['subgroup_name']})" if l.get("subgroup_name") else ""
            lines.append(
                f"• {format_date(l['date'])}, Пара {l['lesson_number']} ({l['start_time']}-{l['end_time']}):\n"
                f"  <b>{l['subject']}</b> ({l['lesson_type']}){sub}\n"
                f"  Преподаватель: {l['teacher'] or '—'}\n"
                f"  Аудитория: {l['room'] or '—'} (корп. {l['building'] or '—'})"
            )
        lines.append("")

    if changes["deleted"]:
        lines.append("<b>❌ Отмененные занятия:</b>")
        for l in changes["deleted"]:
            sub = f" (Подгруппа {l['subgroup_name']})" if l.get("subgroup_name") else ""
            lines.append(
                f"• {format_date(l['date'])}, Пара {l['lesson_number']} ({l['start_time']}-{l['end_time']}):\n"
                f"  <s>{l['subject']}</s> ({l['lesson_type']}){sub}"
            )
        lines.append("")

    if changes["changed"]:
        lines.append("<b>📝 Измененные занятия:</b>")
        for c in changes["changed"]:
            old = c["old"]
            new = c["new"]
            diff = c["diff"]

            sub = f" (Подгруппа {new['subgroup_name']})" if new.get("subgroup_name") else ""
            lines.append(
                f"• {format_date(new['date'])}, Пара {new['lesson_number']} ({new['start_time']}-{new['end_time']}):\n"
                f"  <b>{new['subject']}</b> ({new['lesson_type']}){sub}"
            )

            diff_lines = []
            if "subject" in diff:
                diff_lines.append(f"  Предмет: {diff['subject'][0]} -> <b>{diff['subject'][1]}</b>")
            if "teacher" in diff:
                diff_lines.append(f"  Преподаватель: {diff['teacher'][0] or '—'} -> <b>{diff['teacher'][1] or '—'}</b>")
            if "room" in diff or "building" in diff:
                old_room = f"{old['room'] or '—'} (корп. {old['building'] or '—'})"
                new_room = f"<b>{new['room'] or '—'} (корп. {new['building'] or '—'})</b>"
                diff_lines.append(f"  Кабинет: {old_room} -> {new_room}")
            if "lesson_type" in diff:
                diff_lines.append(f"  Тип занятия: {diff['lesson_type'][0]} -> <b>{diff['lesson_type'][1]}</b>")
            if "start_time" in diff or "end_time" in diff:
                diff_lines.append(f"  Время: {old['start_time']}-{old['end_time']} -> <b>{new['start_time']}-{new['end_time']}</b>")

            lines.extend(diff_lines)
        lines.append("")

    return "\n".join(lines).strip()


async def notify_users_about_changes(changes: dict[str, list]) -> None:
    """Асинхронная рассылка уведомлений всем затронутым пользователям."""
    if not changes["added"] and not changes["deleted"] and not changes["changed"]:
        print("Изменения отсутствуют. Рассылка не требуется.")
        return

    users = await get_all_users()
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        for user in users:
            user_changes = get_user_changes(user, changes)
            if user_changes["added"] or user_changes["deleted"] or user_changes["changed"]:
                text = format_notification(user_changes)
                try:
                    await bot.send_message(chat_id=user["telegram_id"], text=text)
                    print(f"Уведомление успешно отправлено пользователю {user['telegram_id']}")
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {user['telegram_id']}: {e}")
    finally:
        await bot.session.close()
