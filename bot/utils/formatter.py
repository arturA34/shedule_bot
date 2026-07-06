import html
import datetime
from typing import Optional


def get_short_lesson_type(lt: str) -> str:
    """Возвращает сокращенный тип занятия."""
    if not lt:
        return ""
    lt_lower = lt.lower()
    if "лек" in lt_lower:
        return "Лк"
    elif "прак" in lt_lower:
        return "Пр"
    elif "лаб" in lt_lower:
        return "Лб"
    return lt[:2]  # Возвращает первые две буквы как fallback


def format_lessons_student(lessons: list[dict], header: str) -> str:
    """Форматирует список занятий для студента по ТЗ."""
    if not lessons:
        return ""

    blocks = []
    for lesson in lessons:
        num = lesson["lesson_number"]
        start = lesson["start_time"]
        end = lesson["end_time"]
        subject = html.escape(lesson["subject"] or "")
        lesson_type = html.escape(lesson["lesson_type"] or "")
        teacher = html.escape(lesson["teacher"] or "—")
        room = html.escape(lesson["room"] or "—")
        building = html.escape(lesson["building"] or "—")

        block = (
            f"{num} пара ({start}–{end})\n"
            f"{subject} — {lesson_type}\n"
            f"Преподаватель: {teacher}\n"
            f"Аудитория {room}, корпус {building}"
        )
        blocks.append(block)

    return f"{header}\n\n" + "\n\n".join(blocks)


def format_lessons_teacher(lessons: list[dict], header: str) -> str:
    """Форматирует список занятий для преподавателя (Группа вместо Преподаватель)."""
    if not lessons:
        return ""

    blocks = []
    for lesson in lessons:
        num = lesson["lesson_number"]
        start = lesson["start_time"]
        end = lesson["end_time"]
        subject = html.escape(lesson["subject"] or "")
        lesson_type = html.escape(lesson["lesson_type"] or "")
        room = html.escape(lesson["room"] or "—")
        building = html.escape(lesson["building"] or "—")
        group = html.escape(lesson["group_name"] or "—")
        subgroup = lesson.get("subgroup_name")

        group_display = f"{group} ({html.escape(subgroup)})" if subgroup else group

        block = (
            f"{num} пара ({start}–{end})\n"
            f"{subject} — {lesson_type}\n"
            f"Группа: {group_display}\n"
            f"Аудитория {room}, корпус {building}"
        )
        blocks.append(block)

    return f"{header}\n\n" + "\n\n".join(blocks)


def format_week_schedule_student(
    monday: datetime.date,
    week_schedule: dict[str, list[dict]],
    header: str
) -> str:
    """Форматирует компактное расписание на неделю для студента."""
    has_lessons = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(7))
    if not has_lessons:
        return f"{header}\n\n😴 На этой неделе пар нет."

    lines = [header]
    weekdays_labels = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    for i in range(7):
        day = monday + datetime.timedelta(days=i)
        day_str = day.isoformat()
        day_lessons = week_schedule.get(day_str, [])

        date_label = f"📅 {weekdays_labels[i]} ({day.strftime('%d.%m')}):"
        lines.append(date_label)

        if not day_lessons:
            if i in (5, 6):  # Суббота, Воскресенье
                lines.append("😴 Пар нет (выходной)\n")
            else:
                lines.append("😴 Пар нет\n")
        else:
            day_lines = []
            for lesson in day_lessons:
                num = lesson["lesson_number"]
                start = lesson["start_time"]
                end = lesson["end_time"]
                sub = lesson["subject"]
                lt = get_short_lesson_type(lesson["lesson_type"])
                teacher = lesson["teacher"] or "—"
                room = lesson["room"] or "—"
                bld = lesson["building"] or "—"

                day_lines.append(
                    f"{num} пара ({start}–{end}) {sub} — {lt}., {teacher}, {room}, {bld}"
                )
            lines.append("\n".join(day_lines) + "\n")

    return "\n".join(lines).strip()


def format_week_schedule_teacher(
    monday: datetime.date,
    week_schedule: dict[str, list[dict]],
    header: str
) -> str:
    """Форматирует компактное расписание на неделю для преподавателя."""
    has_lessons = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(7))
    if not has_lessons:
        return f"{header}\n\n😴 На этой неделе пар нет."

    lines = [header]
    weekdays_labels = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    for i in range(7):
        day = monday + datetime.timedelta(days=i)
        day_str = day.isoformat()
        day_lessons = week_schedule.get(day_str, [])

        date_label = f"📅 {weekdays_labels[i]} ({day.strftime('%d.%m')}):"
        lines.append(date_label)

        if not day_lessons:
            if i in (5, 6):  # Суббота, Воскресенье
                lines.append("😴 Пар нет (выходной)\n")
            else:
                lines.append("😴 Пар нет\n")
        else:
            day_lines = []
            for lesson in day_lessons:
                num = lesson["lesson_number"]
                start = lesson["start_time"]
                end = lesson["end_time"]
                sub = lesson["subject"]
                lt = get_short_lesson_type(lesson["lesson_type"])
                room = lesson["room"] or "—"
                bld = lesson["building"] or "—"
                group = lesson["group_name"] or "—"
                subgroup = lesson.get("subgroup_name")

                group_display = f"{group} ({subgroup})" if subgroup else group

                day_lines.append(
                    f"{num} пара ({start}–{end}) {sub} — {lt}., {group_display}, {room}, {bld}"
                )
            lines.append("\n".join(day_lines) + "\n")

    return "\n".join(lines).strip()
