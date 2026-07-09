import json
import logging
from datetime import date, timedelta
from typing import Optional

import asyncpg

from bot.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Возвращает пул соединений с БД."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(dsn=settings.db_dsn)
    return _pool


async def close_db() -> None:
    """Закрывает пул соединений с БД."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")


async def get_connection() -> asyncpg.Connection:
    """Возвращает одно соединение с БД."""
    settings = get_settings()
    return await asyncpg.connect(settings.db_dsn)


async def init_db() -> None:
    """Инициализирует схему БД и заполняет начальными данными."""
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

            CREATE TABLE IF NOT EXISTS admin_invites (
                token VARCHAR(255) PRIMARY KEY,
                is_used BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS admins (
                telegram_id BIGINT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS user_links (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_user_links_telegram_id
                ON user_links(telegram_id);
        """)

        # Заполняем преподавателей, если таблица пуста
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

        # Заполняем расписание, если таблица пуста
        schedule_count = await conn.fetchval("SELECT COUNT(*) FROM schedule")
        if schedule_count == 0:
            groups = ["РИ-150943", "РИ-150942"]
            schedule_template = [
                {
                    "day_of_week": "Понедельник",
                    "lessons": [
                        {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Лекция"},
                        {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-01"},
                        {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Физика", "teacher": "Сидоров С.С.", "room": "210", "building": "Корпус Б", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-04"},
                    ],
                },
                {
                    "day_of_week": "Вторник",
                    "lessons": [
                        {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "История", "teacher": "Козлова А.В.", "room": "112", "building": "Главный", "lesson_type": "Лекция"},
                        {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Практика"},
                    ],
                },
                {
                    "day_of_week": "Среда",
                    "lessons": [],
                },
                {
                    "day_of_week": "Четверг",
                    "lessons": [
                        {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лекция"},
                        {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Физика", "teacher": "Сидоров С.С.", "room": "210", "building": "Корпус Б", "lesson_type": "Практика"},
                        {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Философия", "teacher": "Новикова Е.Д.", "room": "201", "building": "Главный", "lesson_type": "Лекция"},
                        {"lesson_number": 4, "start_time": "13:30", "end_time": "15:00", "subject": "Английский язык", "teacher": "Смирнова О.Л.", "room": "108", "building": "Корпус В", "lesson_type": "Практика", "subgroup_name": "ЛБ-02"},
                    ],
                },
                {
                    "day_of_week": "Пятница",
                    "lessons": [
                        {"lesson_number": 1, "start_time": "08:30", "end_time": "10:00", "subject": "Математика", "teacher": "Иванов И.И.", "room": "301", "building": "Главный", "lesson_type": "Практика"},
                        {"lesson_number": 2, "start_time": "10:10", "end_time": "11:40", "subject": "Информатика", "teacher": "Петров П.П.", "room": "405", "building": "Главный", "lesson_type": "Лабораторная", "subgroup_name": "ЛБ-01"},
                        {"lesson_number": 3, "start_time": "11:50", "end_time": "13:20", "subject": "Физкультура", "teacher": "Козлов В.Н.", "room": "Спортзал", "building": "Корпус С", "lesson_type": "Практика"},
                    ],
                },
            ]

            today = date.today()
            monday = today - timedelta(days=today.weekday())

            rows = []
            for group in groups:
                for i, day in enumerate(schedule_template):
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
            logger.info(f"Schedule table seeded with mock data for groups: {', '.join(groups)}.")
    logger.info("Database schema initialized.")


async def get_user(telegram_id: int) -> Optional[dict]:
    """Получить пользователя по telegram_id."""
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
    """Создать или обновить пользователя."""
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
    """Обновить данные пользователя."""
    pool = await get_pool()
    subgroups_json = json.dumps(subgroups, ensure_ascii=False)
    await pool.execute(
        "UPDATE users SET primary_group = $1, subgroups = $2::jsonb WHERE telegram_id = $3",
        primary_group,
        subgroups_json,
        telegram_id,
    )


async def get_all_groups() -> list[str]:
    """Получить список всех групп из расписания."""
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT group_name FROM schedule ORDER BY group_name")
    return [row["group_name"] for row in rows]


async def get_lessons_by_group_and_date(group_name: str, date_str: str) -> list[dict]:
    """Получить занятия группы на указанную дату."""
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
    """Получить занятие по ID."""
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
    """Создать новое занятие."""
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
    """Обновить название предмета у занятия."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET subject = $1 WHERE id = $2",
        subject,
        lesson_id,
    )


async def update_lesson_room_building(lesson_id: int, room: str, building: str) -> None:
    """Обновить аудиторию и корпус у занятия."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET room = $1, building = $2 WHERE id = $3",
        room,
        building,
        lesson_id,
    )


async def update_lesson_teacher(lesson_id: int, teacher: str) -> None:
    """Обновить преподавателя у занятия."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE schedule SET teacher = $1 WHERE id = $2",
        teacher,
        lesson_id,
    )


async def delete_lesson(lesson_id: int) -> None:
    """Удалить занятие."""
    pool = await get_pool()
    await pool.execute(
        "DELETE FROM schedule WHERE id = $1",
        lesson_id,
    )


async def search_teachers(query: str) -> list[dict]:
    """Поиск преподавателей по ФИО."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, fio, department, email FROM teachers WHERE fio ILIKE $1 ORDER BY fio",
        f"%{query}%",
    )
    return [dict(row) for row in rows]


async def get_teacher_by_id(teacher_id: int) -> Optional[dict]:
    """Получить преподавателя по ID."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, fio, department, email FROM teachers WHERE id = $1",
        teacher_id,
    )
    return dict(row) if row else None


async def get_lessons_by_teacher_and_date(teacher_fio: str, date_str: str) -> list[dict]:
    """Получить занятия преподавателя на указанную дату."""
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
    """Получить занятия преподавателя за период."""
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


async def add_admin_invite(token: str) -> None:
    """Добавить инвайт-токен для администратора."""
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO admin_invites (token, is_used) VALUES ($1, FALSE)",
        token,
    )


async def verify_and_claim_invite(token: str, telegram_id: int) -> bool:
    """Проверить и активировать инвайт-токен."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT is_used FROM admin_invites WHERE token = $1",
                token,
            )
            if row is None or row["is_used"]:
                return False

            await conn.execute(
                "UPDATE admin_invites SET is_used = TRUE WHERE token = $1",
                token,
            )
            await conn.execute(
                "INSERT INTO admins (telegram_id) VALUES ($1) ON CONFLICT (telegram_id) DO NOTHING",
                telegram_id,
            )
            return True


async def is_admin(telegram_id: int) -> bool:
    """Проверить, является ли пользователь администратором."""
    pool = await get_pool()
    val = await pool.fetchval(
        "SELECT EXISTS(SELECT 1 FROM admins WHERE telegram_id = $1)",
        telegram_id,
    )
    return bool(val)


async def get_user_links(telegram_id: int) -> list[dict]:
    """Получить все ссылки пользователя."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, title, url FROM user_links WHERE telegram_id = $1 ORDER BY id",
        telegram_id,
    )
    return [{"id": row["id"], "title": row["title"], "url": row["url"]} for row in rows]


async def add_user_link(telegram_id: int, title: str, url: str) -> None:
    """Добавить ссылку пользователю."""
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO user_links (telegram_id, title, url) VALUES ($1, $2, $3)",
        telegram_id,
        title.strip(),
        url.strip(),
    )


async def delete_user_link(telegram_id: int, link_id: int) -> bool:
    """Удалить ссылку по ID."""
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM user_links WHERE id = $1 AND telegram_id = $2",
        link_id,
        telegram_id,
    )
    return result != "DELETE 0"


async def get_user_link_by_url(telegram_id: int, url: str) -> Optional[dict]:
    """Проверить существование ссылки с таким URL."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, title, url FROM user_links WHERE telegram_id = $1 AND url = $2",
        telegram_id,
        url,
    )
    return dict(row) if row else None


async def get_user_link_by_title(telegram_id: int, title: str) -> Optional[dict]:
    """Проверить существование ссылки с таким названием."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, title, url FROM user_links WHERE telegram_id = $1 AND title = $2",
        telegram_id,
        title,
    )
    return dict(row) if row else None