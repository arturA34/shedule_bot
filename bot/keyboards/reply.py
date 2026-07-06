from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает главное меню в виде Reply-клавиатуры."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Расписание на сегодня"),
                KeyboardButton(text="📆 Расписание на завтра"),
            ],
            [
                KeyboardButton(text="📋 Расписание на неделю"),
            ],
            [
                KeyboardButton(text="👨‍🏫 Поиск по преподавателю"),
            ],
            [
                KeyboardButton(text="🔄 Сменить группу"),
                KeyboardButton(text="⚙️ Управление предметами"),
            ],
            [
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
    )


def get_skip_subgroups_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает Reply-клавиатуру для пропуска ввода подгрупп."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⏭️ Без подгрупп"),
            ]
        ],
        resize_keyboard=True,
    )


def get_done_subgroups_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает Reply-клавиатуру для завершения ввода подгрупп."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Готово"),
            ]
        ],
        resize_keyboard=True,
    )



def get_teacher_search_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает Reply-клавиатуру для отмены поиска преподавателя."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❌ Отмена"),
            ]
        ],
        resize_keyboard=True,
    )


def get_teacher_search_retry_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает Reply-клавиатуру для повтора поиска или возврата в меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔄 Попробовать снова"),
                KeyboardButton(text="🔙 В главное меню"),
            ]
        ],
        resize_keyboard=True,
    )


def get_teacher_card_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает Reply-клавиатуру управления карточкой преподавателя."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Расписание сегодня (преп.)"),
                KeyboardButton(text="📆 Расписание завтра (преп.)"),
            ],
            [
                KeyboardButton(text="📋 Расписание неделя (преп.)"),
            ],
            [
                KeyboardButton(text="🔙 В главное меню"),
            ],
        ],
        resize_keyboard=True,
    )
