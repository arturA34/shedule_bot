from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Расписание на сегодня"),
                KeyboardButton(text="Расписание на завтра"),
            ],
            [
                KeyboardButton(text="Расписание на неделю"),
            ],
            [
                KeyboardButton(text="Сменить группу"),
                KeyboardButton(text="Помощь"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )
