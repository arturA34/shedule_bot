from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

menu_router = Router(name="menu")


@menu_router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer(
        "<b>Меню:</b>\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — расписание на завтра\n"
        "/week — расписание на неделю\n"
        "/settings — настройки"
    )
