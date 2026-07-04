from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.reply import get_main_menu_keyboard

help_router = Router(name="help")

HELP_TEXT = (
    "<b>Доступные команды:</b>\n\n"
    "/start — Запуск бота\n"
    "/menu — Главное меню\n"
    "/today — Расписание на сегодня\n"
    "/tomorrow — Расписание на завтра\n"
    "/week — Расписание на неделю\n"
    "/settings — Настройки группы и подгрупп\n"
    "/help — Справка по командам\n\n"
    "<b>Кнопки меню:</b>\n"
    "• Расписание на сегодня / завтра\n"
    "• Расписание на неделю\n"
    "• Сменить группу\n"
    "• Помощь"
)


@help_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=get_main_menu_keyboard())


@help_router.message(lambda m: m.text == "Помощь")
async def btn_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=get_main_menu_keyboard())
