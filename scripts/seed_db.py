import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path, чтобы импортировать модули bot и database
sys.path.append(str(Path(__file__).parent.parent))

from database.db import get_connection, init_db

GROUPS = ["РИ-150943А", "РИ-150943Б"]

SCHEDULE_TEMPLATE = [
    # Monday
    {
        "day_of_week": "Понедельник",
        "lessons": [
            {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Лекция"},
            {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-01"},
            {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Физика", "teacher": "Сидоров С.С.", "room": "210", "building": "Корпус Б", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-04"},
        ],
    },
    # Tuesday
    {
        "day_of_week": "Вторник",
        "lessons": [
            {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "История", "teacher": "Козлова А.В.", "room": "112", "building": "Главный", "lesson_type": "Лекция"},
            {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Практика"},
        ],
    },
    # Wednesday — empty day (no lessons)
    {
        "day_of_week": "Среда",
        "lessons": [],
    },
    # Thursday
    {
        "day_of_week": "Четверг",
        "lessons": [
            {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лекция"},
            {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Физика", "teacher": "Сидоров С.С.", "room": "210", "building": "Корпус Б", "lesson_type": "Практика"},
            {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Философия", "teacher": "Новикова Е.Д.", "room": "201", "building": "Главный", "lesson_type": "Лекция"},
            {"lesson_number": 4, "start_time": "13:30", "end_time": "15:00", "subject": "Английский язык", "teacher": "Смирнова О.Л.", "room": "108", "building": "Корпус В", "lesson_type": "Практика", "subgroup_name": "ЛБ-02"},
        ],
    },
    # Friday
    {
        "day_of_week": "Пятница",
        "lessons": [
            {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Практика"},
            {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-01"},
            {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Физкультура", "teacher": "Козлов В.Н.", "room": "Спортзал", "building": "Корпус С", "lesson_type": "Практика"},
        ],
    },
]


async def seed() -> None:
    await init_db()
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM schedule")

        today = date.today()
        monday = today - timedelta(days=today.weekday())

        rows = []
        for group in GROUPS:
            for i, day in enumerate(SCHEDULE_TEMPLATE):
                current_date = monday + timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                for lesson in day["lessons"]:
                    rows.append((
                        day["day_of_week"],
                        date_str,
                        lesson["lesson_number"],
                        lesson["start_time"],
                        lesson["end_time"],
                        lesson["subject"],
                        lesson["teacher"],
                        lesson["room"],
                        lesson["building"],
                        lesson["lesson_type"],
                        group,
                        lesson.get("subgroup_name"),
                    ))

        await conn.executemany(
            """
            INSERT INTO schedule
                (day_of_week, date, lesson_number, start_time, end_time,
                 subject, teacher, room, building, lesson_type,
                 group_name, subgroup_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            rows,
        )
        print(f"Inserted {len(rows)} rows for groups: {', '.join(GROUPS)}")

        summary = await conn.fetch(
            "SELECT group_name, date, COUNT(*) as cnt FROM schedule GROUP BY group_name, date ORDER BY group_name, date"
        )
        print("\nSummary:")
        print(f"{'Group':<16} {'Date':<12} {'Lessons'}")
        print("-" * 36)
        for row in summary:
            print(f"{row[0]:<16} {row[1]:<12} {row[2]}")
    finally:
        await conn.close()
        from database.db import close_db
        await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
