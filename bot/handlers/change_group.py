from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_main_menu_inline_keyboard, get_skip_subgroups_keyboard
from bot.states.registration import ChangeGroupStates
from database.db import update_user

change_group_router = Router(name="change_group")


async def start_change_group_flow(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    await state.set_state(ChangeGroupStates.WaitingForGroup)
    text = (
        "Смена учебной группы ⚙️\n\n"
        "Пожалуйста, введите номер вашей новой учебной группы\n"
        "(например: <b>РИ-150943А</b>):"
    )
    if message_to_edit:
        try:
            await message_to_edit.edit_text(text)
            await state.update_data(last_msg_id=message_to_edit.message_id)
            return
        except Exception:
            pass

    sent_msg = await (message_to_reply or message_to_edit).answer(text)
    await state.update_data(last_msg_id=sent_msg.message_id)


@change_group_router.message(Command("settings"))
@change_group_router.message(Command("change_group"))
async def cmd_change_group(message: Message, state: FSMContext) -> None:
    await start_change_group_flow(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@change_group_router.callback_query(F.data == "menu:settings")
async def cb_change_group(callback: CallbackQuery, state: FSMContext) -> None:
    await start_change_group_flow(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        message_to_edit=callback.message,
    )
    await callback.answer()


@change_group_router.message(ChangeGroupStates.WaitingForGroup)
async def process_change_group(message: Message, state: FSMContext) -> None:
    group = message.text.strip()
    await state.update_data(primary_group=group)

    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    await state.set_state(ChangeGroupStates.WaitingForSubgroups)
    text = (
        f"Новая группа: <b>{group}</b>\n\n"
        "Теперь укажите ваши новые подгруппы по предметам.\n"
        "Введите их через запятую в формате:\n"
        "<code>Предмет: Подгруппа</code>\n\n"
        "Например: <code>Физика: ЛБ-04, Информатика: ЛБ-01</code>\n\n"
        "Или нажмите кнопку ниже, если у вас нет подгрупп:"
    )

    if last_msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                text=text,
                reply_markup=get_skip_subgroups_keyboard(),
            )
            return
        except Exception:
            pass

    sent_msg = await message.answer(text, reply_markup=get_skip_subgroups_keyboard())
    await state.update_data(last_msg_id=sent_msg.message_id)


@change_group_router.message(ChangeGroupStates.WaitingForSubgroups)
async def process_change_subgroups(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    primary_group = data["primary_group"]
    last_msg_id = data.get("last_msg_id")
    text = message.text.strip()

    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    subgroups = []
    if text.lower() != "нет":
        for item in text.split(","):
            item = item.strip()
            if ":" in item:
                subject, subgroup = item.split(":", 1)
                subgroups.append({
                    "subject": subject.strip(),
                    "subgroup": subgroup.strip(),
                })

    await update_user(message.from_user.id, primary_group, subgroups)
    await state.clear()

    subgroup_info = ""
    if subgroups:
        lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
        subgroup_info = "\n\nНовые подгруппы:\n" + "\n".join(lines)
    else:
        subgroup_info = "\n\nПодгруппы: не указаны."

    success_text = (
        f"Данные успешно обновлены! ⚙️\n\n"
        f"Группа: <b>{primary_group}</b>{subgroup_info}\n\n"
        "Используйте меню ниже для работы с ботом."
    )

    if last_msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                text=success_text,
                reply_markup=get_main_menu_inline_keyboard(),
            )
            return
        except Exception:
            pass

    await message.answer(success_text, reply_markup=get_main_menu_inline_keyboard())


@change_group_router.callback_query(ChangeGroupStates.WaitingForSubgroups, F.data == "subgroups:skip")
async def skip_subgroups_change(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    primary_group = data["primary_group"]

    await update_user(callback.from_user.id, primary_group, [])
    await state.clear()

    await callback.message.edit_text(
        f"Данные успешно обновлены! ⚙️\n\n"
        f"Группа: <b>{primary_group}</b>\n"
        "Подгруппы: не указаны.\n\n"
        "Используйте меню ниже для работы с ботом.",
        reply_markup=get_main_menu_inline_keyboard(),
    )
    await callback.answer()

