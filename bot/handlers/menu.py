from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.reply import get_main_menu_keyboard
from bot.handlers.item_handlers import show_management_menu

menu_router = Router(name="menu")


@menu_router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )


@menu_router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@menu_router.message(Command("settings"))
@menu_router.message(F.text == "⚙️ Управление предметами")
async def handle_items_button(message: Message) -> None:
    """Обработчик кнопки управления предметами"""
    await show_management_menu(message)


@menu_router.message(F.text == "🔙 В главное меню")
async def process_back_to_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )
