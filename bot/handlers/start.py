from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.reply import get_main_menu_keyboard

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        "Я бот расписания. Используй кнопки ниже для навигации.",
        reply_markup=get_main_menu_keyboard(),
    )
