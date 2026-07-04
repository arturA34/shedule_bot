from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_main_menu_inline_keyboard

menu_router = Router(name="menu")


@menu_router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_inline_keyboard()
    )


@menu_router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_inline_keyboard()
    )
    await callback.answer()

