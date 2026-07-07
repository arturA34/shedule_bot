import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup

from bot.keyboards import (
    get_main_menu_keyboard,
    get_skip_subgroups_keyboard,
    get_done_subgroups_keyboard,
    get_cancel_keyboard,
)
from bot.states.registration import ChangeGroupStates, ChangeSubgroupsStates
from database.db import get_user, update_user

change_group_router = Router(name="change_group")
logger = logging.getLogger(__name__)


def parse_subgroup_input(text: str) -> Optional[tuple[str, str]]:
    text = text.strip()
    # Check if they entered it with a colon (e.g. "Физика: ЛБ-04" or "Физика:ЛБ-04")
    if ":" in text:
        parts = text.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    
    parts = text.rsplit(maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip().rstrip(':'), parts[1].strip()
    return None


def render_subgroups_prompt(
    primary_group: str,
    subgroups: list[dict],
    error_text: str = None,
    is_registration: bool = False,
) -> tuple[str, ReplyKeyboardMarkup]:
    lines = []
    if subgroups:
        lines.append("Текущие введенные подгруппы:")
        for s in subgroups:
            lines.append(f"  • {s['subject']}: <b>{s['subgroup']}</b>")
        lines.append("")
    
    subgroups_list_str = "\n".join(lines)
    
    group_prefix = "Выбранная группа" if is_registration else "Новая группа"
    
    text = (
        f"{group_prefix}: <b>{primary_group}</b>\n\n"
        f"{subgroups_list_str}"
        "Теперь укажите ваши новые подгруппы по предметам.\n"
        "Введите их по одной в формате:\n"
        "<code>Предмет Подгруппа</code>\n\n"
        "Например: <code>Физика ЛБ-04</code>\n\n"
    )
    if error_text:
        text += f"⚠️ <b>Ошибка:</b> {error_text}\n\n"
    
    if subgroups:
        text += "Или нажмите кнопку ниже, если вы ввели все свои подгруппы:"
        reply_markup = get_done_subgroups_keyboard()
    else:
        text += "Или нажмите кнопку ниже, если у вас нет подгрупп:"
        reply_markup = get_skip_subgroups_keyboard()
        
    return text, reply_markup


async def update_subgroups_message(
    message: Message,
    state: FSMContext,
    primary_group: str,
    subgroups: list[dict],
    error_text: str = None,
    is_registration: bool = False,
) -> None:
    text, reply_markup = render_subgroups_prompt(
        primary_group, subgroups, error_text, is_registration
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    
    if last_msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass
            
    sent_msg = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_msg_id=sent_msg.message_id)


async def start_change_group_flow(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    await state.set_state(ChangeGroupStates.WaitingForGroup)
    text = (
        "Смена учебной группы 🔄\n\n"
        "Пожалуйста, введите номер вашей новой учебной группы\n"
        "(например: <b>РИ-150943</b>):"
    )
    if message_to_edit:
        try:
            await message_to_edit.delete()
        except Exception:
            pass

    sent_msg = await (message_to_reply or message_to_edit).answer(
        text, reply_markup=get_cancel_keyboard()
    )
    await state.update_data(last_msg_id=sent_msg.message_id)


@change_group_router.message(Command("change_group"))
@change_group_router.message(F.text == "🔄 Сменить группу")
async def cmd_change_group(message: Message, state: FSMContext) -> None:
    await start_change_group_flow(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@change_group_router.message(ChangeGroupStates.WaitingForGroup)
async def process_change_group(message: Message, state: FSMContext) -> None:
    new_group = message.text.strip()

    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    if new_group == "❌ Отмена":
        data = await state.get_data()
        last_msg_id = data.get("last_msg_id")
        await state.clear()

        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass

        await message.answer(
            "<b>Главное меню</b> 📱\n\n"
            "Выберите интересующий раздел:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Retrieve current user to keep their subgroups
    user = await get_user(message.from_user.id)
    subgroups = user["subgroups"] if user else []

    await update_user(message.from_user.id, new_group, subgroups)
    
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await state.clear()

    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    subgroup_info = ""
    if subgroups:
        lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
        subgroup_info = "\n\nТекущие подгруппы:\n" + "\n".join(lines)
    else:
        subgroup_info = "\n\nПодгруппы: не указаны."

    success_text = (
        f"Группа успешно обновлена! ⚙️\n\n"
        f"Группа: <b>{new_group}</b>{subgroup_info}\n\n"
        "Используйте меню ниже для работы с ботом."
    )
    await message.answer(success_text, reply_markup=get_main_menu_keyboard())


@change_group_router.message(F.text == "⚙️ Управление предметами")
async def cmd_change_subgroups(message: Message, state: FSMContext) -> None:
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(
            "Вы не зарегистрированы. Пожалуйста, введите /start для начала работы с ботом."
        )
        return

    primary_group = user["primary_group"]
    await state.set_state(ChangeSubgroupsStates.WaitingForSubgroups)
    await state.update_data(primary_group=primary_group, subgroups=[])

    # Delete original message to keep clean if possible
    try:
        await message.delete()
    except Exception:
        pass

    await update_subgroups_message(message, state, primary_group, [], is_registration=False)


@change_group_router.message(ChangeSubgroupsStates.WaitingForSubgroups)
async def process_change_subgroups(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    primary_group = data["primary_group"]
    subgroups = data.get("subgroups", [])
    text = message.text.strip()

    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    # Check if the user is finished
    if text.lower() in ("нет", "⏭️ без подгрупп", "✅ готово"):
        # Apply changes to DB
        await update_user(message.from_user.id, primary_group, subgroups)
        
        last_msg_id = data.get("last_msg_id")
        await state.clear()

        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass

        subgroup_info = ""
        if subgroups:
            lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
            subgroup_info = "\n\nНовые подгруппы:\n" + "\n".join(lines)
        else:
            subgroup_info = "\n\nПодгруппы: не указаны."

        success_text = (
            f"Подгруппы успешно обновлены! ⚙️\n\n"
            f"Группа: <b>{primary_group}</b>{subgroup_info}\n\n"
            "Используйте меню ниже для работы с ботом."
        )
        await message.answer(success_text, reply_markup=get_main_menu_keyboard())
        return

    # Parse subgroup
    parsed = parse_subgroup_input(text)
    if not parsed:
        error_text = "Неверный формат. Пожалуйста, введите в формате: Предмет Подгруппа (например: Физика ЛБ-04)"
        await update_subgroups_message(
            message, state, primary_group, subgroups, error_text=error_text, is_registration=False
        )
        return

    subject, subgroup = parsed
    
    # Replace subgroup if the subject already exists, to avoid duplicates
    updated = False
    for s in subgroups:
        if s["subject"].lower() == subject.lower():
            s["subgroup"] = subgroup
            updated = True
            break
    if not updated:
        subgroups.append({"subject": subject, "subgroup": subgroup})

    await state.update_data(subgroups=subgroups)
    await update_subgroups_message(message, state, primary_group, subgroups, is_registration=False)
