from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

help_router = Router(name="help")

HELP_TEXT = (
    "❓ <b>Справка по использованию бота</b>\n\n"
    "<b>Доступные команды:</b>\n"
    "• /start — Запустить бота\n"
    "• /menu — Главное меню\n"
    "• /today — Расписание на сегодня\n"
    "• /tomorrow — Расписание на завтра\n"
    "• /week — Расписание на неделю\n"
    "• /settings — Настройки группы и подгрупп\n"
    "• /help — Показать эту справку\n\n"
    "Все эти функции также доступны с помощью меню внизу экрана!"
)


@help_router.message(Command("help"))
@help_router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@help_router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(HELP_TEXT)
    await callback.answer()
