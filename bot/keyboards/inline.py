import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def get_week_navigation_keyboard(
    monday: datetime.date,
    day_index: int,
    has_prev_day: bool,
    has_next_day: bool,
) -> InlineKeyboardMarkup:
    """Клавиатура навигации по дням недели.

    Args:
        monday: дата понедельника текущей недели.
        day_index: индекс текущего дня (0=Пн .. 6=Вс).
        has_prev_day: есть ли день назад с занятиями.
        has_next_day: есть ли день вперёд с занятиями.
    """
    current_date = monday + datetime.timedelta(days=day_index)
    day_label = f"{WEEKDAY_SHORT[day_index]} {current_date.strftime('%d.%m')}"

    buttons: list[InlineKeyboardButton] = []

    if has_prev_day:
        prev_index = day_index - 1
        buttons.append(
            InlineKeyboardButton(
                text="◀ Назад",
                callback_data=f"week:{monday.isoformat()}:{prev_index}",
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=day_label,
            callback_data=f"week_info:{monday.isoformat()}:{day_index}",
        )
    )

    if has_next_day:
        next_index = day_index + 1
        buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶",
                callback_data=f"week:{monday.isoformat()}:{next_index}",
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[buttons])
