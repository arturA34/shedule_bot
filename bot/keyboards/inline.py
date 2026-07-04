import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Возвращает главное меню в виде инлайн-клавиатуры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="menu:today"),
                InlineKeyboardButton(text="🌅 Завтра", callback_data="menu:tomorrow"),
            ],
            [
                InlineKeyboardButton(text="🗓️ На неделю", callback_data="menu:week"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Сменить группу", callback_data="menu:settings"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
            ],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн-кнопку возврата в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 В меню", callback_data="menu:main"),
            ]
        ]
    )


def get_skip_subgroups_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн-кнопку для пропуска ввода подгрупп."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏭️ Без подгрупп", callback_data="subgroups:skip"),
            ]
        ]
    )


def get_week_navigation_keyboard(
    monday: datetime.date,
    day_index: int,
    has_prev_day: bool,
    has_next_day: bool,
) -> InlineKeyboardMarkup:
    """Клавиатура навигации по дням недели с кнопкой возврата в меню."""
    current_date = monday + datetime.timedelta(days=day_index)
    day_label = f"{WEEKDAY_SHORT[day_index]} {current_date.strftime('%d.%m')}"

    nav_row: list[InlineKeyboardButton] = []

    if has_prev_day:
        prev_index = day_index - 1
        nav_row.append(
            InlineKeyboardButton(
                text="◀ Назад",
                callback_data=f"week:{monday.isoformat()}:{prev_index}",
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            text=day_label,
            callback_data=f"week_info:{monday.isoformat()}:{day_index}",
        )
    )

    if has_next_day:
        next_index = day_index + 1
        nav_row.append(
            InlineKeyboardButton(
                text="Вперёд ▶",
                callback_data=f"week:{monday.isoformat()}:{next_index}",
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav_row,
            [
                InlineKeyboardButton(text="🔙 В меню", callback_data="menu:main"),
            ]
        ]
    )


# --- Классы CallbackData для Админ-Панели ---
from aiogram.filters.callback_data import CallbackData


class AdminGroupSelCb(CallbackData, prefix="adm_grp"):
    action: str
    group_name: str


class AdminNavCb(CallbackData, prefix="adm_nav"):
    action: str
    group_name: str
    date_str: str


class AdminLessonCb(CallbackData, prefix="adm_les"):
    action: str
    lesson_id: int
    date_str: str
    group_name: str


# --- Клавиатуры для Админ-Панели ---

def get_admin_groups_keyboard(groups: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура со списком групп и кнопкой создания новой."""
    keyboard_buttons = []
    # Отображаем группы сеткой по 2 в ряд
    for i in range(0, len(groups), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=groups[i],
                callback_data=AdminGroupSelCb(action="select", group_name=groups[i]).pack(),
            )
        )
        if i + 1 < len(groups):
            row.append(
                InlineKeyboardButton(
                    text=groups[i+1],
                    callback_data=AdminGroupSelCb(action="select", group_name=groups[i+1]).pack(),
                )
            )
        keyboard_buttons.append(row)

    # Ряд создания новой группы
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="➕ Создать новую группу",
            callback_data=AdminGroupSelCb(action="create", group_name="").pack(),
        )
    ])
    # Ряд возврата в меню
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_admin_schedule_keyboard(group_name: str, date_str: str, lessons: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура расписания группы на день: список пар, навигация, добавление."""
    keyboard_buttons = []

    # Выводим пары в этот день
    for lesson in lessons:
        sub = f" ({lesson['subgroup_name']})" if lesson.get("subgroup_name") else ""
        room_info = f" [каб. {lesson['room']}]" if lesson.get("room") else ""
        button_text = f"[{lesson['lesson_number']}] {lesson['start_time']} {lesson['subject']}{sub}{room_info}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=AdminLessonCb(
                    action="view",
                    lesson_id=lesson["id"],
                    date_str=date_str,
                    group_name=group_name,
                ).pack(),
            )
        ])

    # Управляющий ряд (Назад / Дата / Вперед)
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=AdminNavCb(action="prev", group_name=group_name, date_str=date_str).pack(),
        ),
        InlineKeyboardButton(
            text="📅 Дата",
            callback_data=AdminNavCb(action="current", group_name=group_name, date_str=date_str).pack(),
        ),
        InlineKeyboardButton(
            text="▶️ Вперед",
            callback_data=AdminNavCb(action="next", group_name=group_name, date_str=date_str).pack(),
        ),
    ])

    # Кнопки действия (Добавить пару)
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="➕ Добавить пару",
            callback_data=AdminNavCb(action="add", group_name=group_name, date_str=date_str).pack(),
        )
    ])

    # Кнопка возврата к списку групп
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🏠 К выбору группы",
            callback_data=AdminGroupSelCb(action="list", group_name="").pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_admin_lesson_keyboard(lesson_id: int, date_str: str, group_name: str) -> InlineKeyboardMarkup:
    """Клавиатура управления конкретной парой."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать предмет",
                    callback_data=AdminLessonCb(action="edit_subject", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать аудиторию",
                    callback_data=AdminLessonCb(action="edit_room", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать преподавателя",
                    callback_data=AdminLessonCb(action="edit_teacher", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Удалить пару",
                    callback_data=AdminLessonCb(action="delete", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к расписанию дня",
                    callback_data=AdminNavCb(action="view", group_name=group_name, date_str=date_str).pack(),
                )
            ],
        ]
    )


def get_admin_delete_confirm_keyboard(lesson_id: int, date_str: str, group_name: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления пары."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить ❌",
                    callback_data=AdminLessonCb(action="confirm_delete", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                ),
                InlineKeyboardButton(
                    text="Отмена ↩️",
                    callback_data=AdminLessonCb(action="view", lesson_id=lesson_id, date_str=date_str, group_name=group_name).pack(),
                ),
            ]
        ]
    )


def get_admin_lesson_number_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора номера пары."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 (08:30-10:00)", callback_data="lesson_num:1"),
                InlineKeyboardButton(text="2 (10:10-11:40)", callback_data="lesson_num:2"),
            ],
            [
                InlineKeyboardButton(text="3 (11:50-13:20)", callback_data="lesson_num:3"),
                InlineKeyboardButton(text="4 (13:30-15:00)", callback_data="lesson_num:4"),
            ],
            [
                InlineKeyboardButton(text="5 (15:10-16:40)", callback_data="lesson_num:5"),
                InlineKeyboardButton(text="6 (16:50-18:20)", callback_data="lesson_num:6"),
            ],
        ]
    )


def get_admin_lesson_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа пары."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Лекция", callback_data="lesson_type:Лекция"),
                InlineKeyboardButton(text="Практика", callback_data="lesson_type:Практика"),
                InlineKeyboardButton(text="Лабораторная", callback_data="lesson_type:Лабораторная"),
            ]
        ]
    )


def get_admin_subgroup_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора подгруппы."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Для всей группы", callback_data="lesson_subgroup:all"),
            ]
        ]
    )


