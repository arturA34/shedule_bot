import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path, чтобы импортировать модули bot и database
sys.path.append(str(Path(__file__).parent.parent))

from database.db import get_connection, close_db
from bot.services.notification_service import (
    detect_schedule_changes,
    notify_users_about_changes,
)

GROUP = "РИ-150943А"
TARGET_DATE = "2026-07-06"  # Понедельник первой полной недели


async def main() -> None:
    conn = await get_connection()
    try:
        print("Шаг 1: Чтение исходного расписания...")
        # Получаем все занятия группы
        old_rows = await conn.fetch(
            "SELECT * FROM schedule WHERE group_name = $1 ORDER BY date, lesson_number",
            GROUP,
        )
        old_lessons = [dict(row) for row in old_rows]

        # Ищем конкретные занятия для изменения и удаления
        lesson_to_modify = None
        lesson_to_delete = None

        for lesson in old_lessons:
            if lesson["date"] == TARGET_DATE:
                if lesson["lesson_number"] == 1:
                    lesson_to_modify = lesson
                elif lesson["lesson_number"] == 3:
                    lesson_to_delete = lesson

        if not lesson_to_modify or not lesson_to_delete:
            print("Ошибка: В базе данных нет ожидаемых занятий для симуляции на 2026-07-06.")
            print("Пожалуйста, убедитесь, что вы предварительно заполнили базу моковыми данными.")
            return

        print("Шаг 2: Симуляция обновления расписания в БД администратором...")
        # 1. Изменяем кабинет (с 301 на 402) для первой пары
        await conn.execute(
            "UPDATE schedule SET room = $1 WHERE id = $2",
            "402", lesson_to_modify["id"],
        )

        # 2. Удаляем третью пару (Информатика)
        await conn.execute(
            "DELETE FROM schedule WHERE id = $1",
            lesson_to_delete["id"],
        )

        # 3. Добавляем новое занятие (4-я пара)
        await conn.execute(
            """
            INSERT INTO schedule (day_of_week, date, lesson_number, start_time, end_time,
                                 subject, teacher, room, building, lesson_type, group_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            "Понедельник",
            TARGET_DATE,
            4,
            "13:30",
            "15:00",
            "Физическая культура",
            "Белов С.И.",
            "Спортзал",
            "—",
            "Практика",
            GROUP,
        )
        print("База данных временно обновлена.")

        print("Шаг 3: Получение нового состояния расписания и расчет разницы (diff)...")
        new_rows = await conn.fetch(
            "SELECT * FROM schedule WHERE group_name = $1 ORDER BY date, lesson_number",
            GROUP,
        )
        new_lessons = [dict(row) for row in new_rows]

        # Сравниваем версии
        changes = detect_schedule_changes(old_lessons, new_lessons)
        
        print("\nОбнаруженные изменения:")
        print(f"Добавлено: {len(changes['added'])} занятий")
        print(f"Удалено: {len(changes['deleted'])} занятий")
        print(f"Изменено: {len(changes['changed'])} занятий")

        print("\nШаг 4: Рассылка уведомлений пользователям...")
        await notify_users_about_changes(changes)

        print("\nШаг 5: Восстановление исходного состояния БД (откат изменений)...")
        # Восстанавливаем измененный кабинет
        await conn.execute(
            "UPDATE schedule SET room = $1 WHERE id = $2",
            lesson_to_modify["room"], lesson_to_modify["id"],
        )

        # Восстанавливаем удаленное занятие
        await conn.execute(
            """
            INSERT INTO schedule (id, day_of_week, date, lesson_number, start_time, end_time,
                                 subject, teacher, room, building, lesson_type, group_name, subgroup_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            lesson_to_delete["id"],
            lesson_to_delete["day_of_week"],
            lesson_to_delete["date"],
            lesson_to_delete["lesson_number"],
            lesson_to_delete["start_time"],
            lesson_to_delete["end_time"],
            lesson_to_delete["subject"],
            lesson_to_delete["teacher"],
            lesson_to_delete["room"],
            lesson_to_delete["building"],
            lesson_to_delete["lesson_type"],
            lesson_to_delete["group_name"],
            lesson_to_delete["subgroup_name"],
        )

        # Удаляем добавленную физкультуру
        await conn.execute(
            "DELETE FROM schedule WHERE date = $1 AND lesson_number = $2 AND group_name = $3",
            TARGET_DATE, 4, GROUP,
        )
        print("База данных успешно восстановлена в первоначальное состояние.")
    finally:
        await conn.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
