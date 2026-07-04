import html


def format_schedule(lessons: list[dict], date_label: str) -> str:
    """Форматирует список занятий в HTML-разметку по ТЗ (раздел 8.3)."""
    if not lessons:
        return ""

    header = f"<b>Расписание на {date_label}:</b>\n"
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
            f"{num} пара ({start}-{end})\n"
            f"{subject} — {lesson_type}\n"
            f"Преподаватель: {teacher}\n"
            f"Аудитория {room}, корпус {building}"
        )
        blocks.append(block)

    return header + "\n\n".join(blocks)
