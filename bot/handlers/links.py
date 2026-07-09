import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.links_keyboards import (
    get_links_main_keyboard,
    get_links_delete_keyboard,
    get_cancel_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.links import LinkStates
from database.db import get_user_links, add_user_link, delete_user_link, get_user_link_by_url, get_user_link_by_title

logger = logging.getLogger(__name__)

links_router = Router(name="links")


async def show_links_main(message: Message, user_id: int, edit: bool = False) -> None:
    """Показывает главное меню со списком ссылок."""
    links = await get_user_links(user_id)
    
    text = "🔗 <b>Полезные ссылки</b>\n\n"
    text += "📚 <b>Стандартные ссылки УрФУ:</b>\n"
    text += "• <a href='https://istudent.urfu.ru/'>Личный кабинет студента УрФУ</a>\n"
    text += "• <a href='https://urfu.modeus.org/'>Модеус</a>"
    
    if links:
        text += "\n\n<b>➕ Ваши ссылки:</b>\n"
        for link in links:
            text += f"• <a href='{link['url']}'>{link['title']}</a>\n"
    else:
        text += "\n\n📭 У вас пока нет сохранённых ссылок."
    
    if edit:
        await message.edit_text(text, reply_markup=get_links_main_keyboard(), parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer(text, reply_markup=get_links_main_keyboard(), parse_mode="HTML", disable_web_page_preview=True)


async def delete_messages(state: FSMContext, bot, chat_id: int) -> None:
    """Удаляет все сохранённые служебные сообщения."""
    data = await state.get_data()
    msg_ids = data.get("msg_ids", [])
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    await state.update_data(msg_ids=[])


async def save_message(state: FSMContext, message_id: int) -> None:
    """Сохраняет ID сообщения для последующего удаления."""
    data = await state.get_data()
    msg_ids = data.get("msg_ids", [])
    msg_ids.append(message_id)
    await state.update_data(msg_ids=msg_ids)


@links_router.message(Command("links"))
@links_router.message(F.text.contains("Полезные ссылки"))
async def cmd_links(message: Message, state: FSMContext) -> None:
    """Обработчик команды /links и кнопки 'Полезные ссылки'."""
    await state.clear()
    await show_links_main(message, message.from_user.id)


@links_router.callback_query(F.data == "links:main")
async def cb_links_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню ссылок."""
    await state.clear()
    await show_links_main(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


@links_router.callback_query(F.data == "links:back")
async def cb_links_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню бота."""
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Главное меню</b> 📱\n\nВыберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@links_router.callback_query(F.data == "links:add")
async def cb_links_add(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинает процесс добавления ссылки."""
    await state.clear()
    await state.set_state(LinkStates.WaitingForURL)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    sent_msg = await callback.message.answer(
        "🔗 Введите ссылку (URL):\n"
        "Например: <code>https://example.com</code>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await save_message(state, sent_msg.message_id)
    await callback.answer()


@links_router.message(LinkStates.WaitingForURL)
async def process_link_url(message: Message, state: FSMContext) -> None:
    """Обработка ввода URL."""
    url = message.text.strip()
    
    try:
        await message.delete()
    except Exception:
        pass
    
    if not url.startswith(("http://", "https://")):
        sent_msg = await message.answer("❌ Ссылка должна начинаться с http:// или https://")
        await save_message(state, sent_msg.message_id)
        return
    
    existing = await get_user_link_by_url(message.from_user.id, url)
    if existing:
        await delete_messages(state, message.bot, message.chat.id)
        sent_msg = await message.answer(
            f"❌ Ссылка с таким URL уже существует: <b>{existing['title']}</b>",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await save_message(state, sent_msg.message_id)
        sent_msg2 = await message.answer(
            "🔗 Введите другую ссылку (URL):\n"
            "Например: <code>https://example.com</code>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await save_message(state, sent_msg2.message_id)
        return
    
    await state.update_data(url=url)
    await state.set_state(LinkStates.WaitingForTitle)
    
    await delete_messages(state, message.bot, message.chat.id)
    
    sent_msg = await message.answer(
        "🔗 Введите название для ссылки:",
        reply_markup=get_cancel_keyboard()
    )
    await save_message(state, sent_msg.message_id)


@links_router.message(LinkStates.WaitingForTitle)
async def process_link_title(message: Message, state: FSMContext) -> None:
    """Обработка ввода названия."""
    title = message.text.strip()
    
    try:
        await message.delete()
    except Exception:
        pass
    
    if not title:
        sent_msg = await message.answer("❌ Название не может быть пустым.")
        await save_message(state, sent_msg.message_id)
        return
    
    if title.startswith(("http://", "https://")):
        sent_msg = await message.answer("❌ Название не может быть ссылкой. Введите текстовое название.")
        await save_message(state, sent_msg.message_id)
        return
    
    existing = await get_user_link_by_title(message.from_user.id, title)
    if existing:
        await delete_messages(state, message.bot, message.chat.id)
        sent_msg = await message.answer(
            f"❌ Ссылка с таким названием уже существует: <b>{existing['title']}</b>",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await save_message(state, sent_msg.message_id)
        sent_msg2 = await message.answer(
            "🔗 Введите другое название для ссылки:",
            reply_markup=get_cancel_keyboard()
        )
        await save_message(state, sent_msg2.message_id)
        return
    
    data = await state.get_data()
    await add_user_link(message.from_user.id, title, data.get("url"))
    
    await delete_messages(state, message.bot, message.chat.id)
    await state.clear()
    
    await show_links_main(message, message.from_user.id)


@links_router.callback_query(F.data == "links:delete")
async def cb_links_delete_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинает процесс удаления ссылки."""
    await state.clear()
    links = await get_user_links(callback.from_user.id)
    
    if not links:
        await callback.answer("У вас нет сохранённых ссылок для удаления.", show_alert=True)
        return
    
    await state.set_state(LinkStates.WaitingForDelete)
    
    text = "🗑️ <b>Выберите ссылку для удаления:</b>"
    await callback.message.edit_text(text, reply_markup=get_links_delete_keyboard(links), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@links_router.callback_query(F.data.startswith("links:delete_confirm:"))
async def cb_links_delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение удаления ссылки."""
    link_id = int(callback.data.split(":")[2])
    await delete_user_link(callback.from_user.id, link_id)
    await callback.answer("✅ Ссылка удалена!")
    
    await state.clear()
    
    links = await get_user_links(callback.from_user.id)
    if links:
        text = "🗑️ <b>Выберите ссылку для удаления:</b>"
        await callback.message.edit_text(text, reply_markup=get_links_delete_keyboard(links), parse_mode="HTML", disable_web_page_preview=True)
    else:
        await callback.message.delete()
        await show_links_main(callback.message, callback.from_user.id)


@links_router.callback_query(F.data == "links:cancel")
async def cb_links_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена операции."""
    await delete_messages(state, callback.bot, callback.message.chat.id)
    await state.clear()
    await show_links_main(callback.message, callback.from_user.id, edit=True)
    await callback.answer()