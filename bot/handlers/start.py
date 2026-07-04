from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        "Я бот расписания. Используй /menu для навигации."
    )
