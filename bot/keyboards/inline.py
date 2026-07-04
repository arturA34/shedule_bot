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

