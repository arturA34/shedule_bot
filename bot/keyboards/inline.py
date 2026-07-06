import datetime
from typing import Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Возвращает главное меню в виде инлайн-клавиатуры."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Расписание на сегодня", callback_data="menu:today"),
                InlineKeyboardButton(text="📆 Расписание на завтра", callback_data="menu:tomorrow"),
            ],
            [
                InlineKeyboardButton(text="📋 Расписание на неделю", callback_data="menu:week"),
            ],
            [
                InlineKeyboardButton(text="👨‍🏫 Поиск по преподавателю", callback_data="menu:teacher_search"),
                InlineKeyboardButton(text="⚙️ Управление подгруппами", callback_data="menu:settings"),
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
            ],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн-кнопку возврата в меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
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


def get_today_schedule_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн-кнопки под сообщением расписания на сегодня."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📆 Завтра", callback_data="menu:tomorrow"),
                InlineKeyboardButton(text="📋 Неделя", callback_data="menu:week"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_tomorrow_schedule_keyboard() -> InlineKeyboardMarkup:
    """Возвращает инлайн-кнопки под сообщением расписания на завтра."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="menu:today"),
                InlineKeyboardButton(text="📋 Неделя", callback_data="menu:week"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_today_holiday_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📆 Да, показать завтра", callback_data="menu:tomorrow"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_tomorrow_holiday_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Показать сегодня", callback_data="menu:today"),
                InlineKeyboardButton(text="📋 Неделя", callback_data="menu:week"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_week_navigation_keyboard(
    monday: datetime.date,
    day_index: Optional[int] = None,
) -> InlineKeyboardMarkup:
    """Клавиатура навигации по неделям и дням."""
    prev_monday = monday - datetime.timedelta(days=7)
    next_monday = monday + datetime.timedelta(days=7)
    
    if day_index is None:
        left_callback = f"week:show:{prev_monday.isoformat()}"
        right_callback = f"week:show:{next_monday.isoformat()}"
    else:
        left_callback = f"week:day:{prev_monday.isoformat()}:{day_index}"
        right_callback = f"week:day:{next_monday.isoformat()}:{day_index}"
        
    row1 = [
        InlineKeyboardButton(text="◀️", callback_data=left_callback)
    ]
    
    weekdays_short = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    for idx, day_label in enumerate(weekdays_short):
        row1.append(
            InlineKeyboardButton(
                text=day_label,
                callback_data=f"week:day:{monday.isoformat()}:{idx}"
            )
        )
        
    row1.append(InlineKeyboardButton(text="▶️", callback_data=right_callback))
    
    row2 = []
    if day_index is not None:
        row2.append(
            InlineKeyboardButton(text="📋 Вся неделя", callback_data=f"week:show:{monday.isoformat()}")
        )
    row2.append(InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"))
    
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


def get_teacher_search_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="teacher_search:cancel")
            ]
        ]
    )


def get_teacher_search_retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="teacher_search:retry"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_teacher_card_keyboard(teacher_id: int, monday_str: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data=f"t_sch:today:{teacher_id}"),
                InlineKeyboardButton(text="📆 Завтра", callback_data=f"t_sch:tomorrow:{teacher_id}"),
                InlineKeyboardButton(text="📋 Неделя", callback_data=f"t_sch:week:show:{teacher_id}:{monday_str}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
            ]
        ]
    )


def get_teacher_today_keyboard(teacher_id: int, monday_str: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📆 Завтра", callback_data=f"t_sch:tomorrow:{teacher_id}"),
                InlineKeyboardButton(text="📋 Неделя", callback_data=f"t_sch:week:show:{teacher_id}:{monday_str}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data=f"t_sch:card:{teacher_id}"),
            ]
        ]
    )


def get_teacher_tomorrow_keyboard(teacher_id: int, monday_str: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data=f"t_sch:today:{teacher_id}"),
                InlineKeyboardButton(text="📋 Неделя", callback_data=f"t_sch:week:show:{teacher_id}:{monday_str}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data=f"t_sch:card:{teacher_id}"),
            ]
        ]
    )


def get_teacher_week_navigation_keyboard(
    teacher_id: int,
    monday: datetime.date,
    day_index: Optional[int] = None,
) -> InlineKeyboardMarkup:
    prev_monday = monday - datetime.timedelta(days=7)
    next_monday = monday + datetime.timedelta(days=7)
    
    if day_index is None:
        left_callback = f"t_sch:week:show:{teacher_id}:{prev_monday.isoformat()}"
        right_callback = f"t_sch:week:show:{teacher_id}:{next_monday.isoformat()}"
    else:
        left_callback = f"t_sch:week:day:{teacher_id}:{prev_monday.isoformat()}:{day_index}"
        right_callback = f"t_sch:week:day:{teacher_id}:{next_monday.isoformat()}:{day_index}"
        
    row1 = [
        InlineKeyboardButton(text="◀️", callback_data=left_callback)
    ]
    
    weekdays_short = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    for idx, day_label in enumerate(weekdays_short):
        row1.append(
            InlineKeyboardButton(
                text=day_label,
                callback_data=f"t_sch:week:day:{teacher_id}:{monday.isoformat()}:{idx}"
            )
        )
        
    row1.append(InlineKeyboardButton(text="▶️", callback_data=right_callback))
    
    row2 = []
    if day_index is not None:
        row2.append(
            InlineKeyboardButton(text="📋 Вся неделя", callback_data=f"t_sch:week:show:{teacher_id}:{monday.isoformat()}")
        )
    row2.append(InlineKeyboardButton(text="🔙 Назад", callback_data=f"t_sch:card:{teacher_id}"))
    
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


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


