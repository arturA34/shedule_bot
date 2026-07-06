import json

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import get_main_menu_keyboard, get_skip_subgroups_keyboard
from bot.states.registration import RegistrationStates
from database.db import get_user, create_user

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {message.from_user.full_name}! 👋\n\n"
            f"Ваша текущая группа: <b>{user['primary_group']}</b>\n"
            "Выберите интересующий раздел в меню ниже:",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await state.set_state(RegistrationStates.WaitingForGroup)
    sent_msg = await message.answer(
        f"Привет, {message.from_user.full_name}! 🎓\n\n"
        "Я бот расписания. Я помогу вам всегда быть в курсе учебного расписания.\n\n"
        "Пожалуйста, введите номер вашей учебной группы\n"
        "(например: <b>РИ-150943А</b>):"
    )
    await state.update_data(last_msg_id=sent_msg.message_id)


@start_router.message(RegistrationStates.WaitingForGroup)
async def process_group(message: Message, state: FSMContext) -> None:
    group = message.text.strip()
    await state.update_data(primary_group=group)
    
    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    await state.set_state(RegistrationStates.WaitingForSubgroups)
    text = (
        f"Выбранная группа: <b>{group}</b>\n\n"
        "Теперь укажите ваши подгруппы по предметам.\n"
        "Введите их через запятую в формате:\n"
        "<code>Предмет: Подгруппа</code>\n\n"
        "Например: <code>Физика: ЛБ-04, Информатика: ЛБ-01</code>\n\n"
        "Или нажмите кнопку ниже, если у вас нет подгрупп:"
    )

    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    sent_msg = await message.answer(text, reply_markup=get_skip_subgroups_keyboard())
    await state.update_data(last_msg_id=sent_msg.message_id)


@start_router.message(RegistrationStates.WaitingForSubgroups)
async def process_subgroups(message: Message, state: FSMContext) -> None:
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
    if text.lower() not in ("нет", "⏭️ без подгрупп"):
        for item in text.split(","):
            item = item.strip()
            if ":" in item:
                subject, subgroup = item.split(":", 1)
                subgroups.append({
                    "subject": subject.strip(),
                    "subgroup": subgroup.strip(),
                })

    await create_user(message.from_user.id, primary_group, subgroups)
    await state.clear()

    subgroup_info = ""
    if subgroups:
        lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
        subgroup_info = "\n\nВаши подгруппы:\n" + "\n".join(lines)
    else:
        subgroup_info = "\n\nПодгруппы: не указаны."

    success_text = (
        f"Регистрация успешно завершена! 🎉\n\n"
        f"Группа: <b>{primary_group}</b>{subgroup_info}\n\n"
        "Используйте меню ниже для работы с ботом."
    )

    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass

    await message.answer(success_text, reply_markup=get_main_menu_keyboard())


@start_router.callback_query(RegistrationStates.WaitingForSubgroups, F.data == "subgroups:skip")
async def skip_subgroups_registration(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    primary_group = data["primary_group"]

    await create_user(callback.from_user.id, primary_group, [])
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"Регистрация успешно завершена! 🎉\n\n"
        f"Группа: <b>{primary_group}</b>\n"
        "Подгруппы: не указаны.\n\n"
        "Используйте меню ниже для работы с ботом.",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
