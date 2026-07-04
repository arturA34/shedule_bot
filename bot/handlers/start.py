import json

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.registration import RegistrationStates
from database.db import get_user, create_user

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {message.from_user.full_name}!\n"
            f"Ваша группа: <b>{user['primary_group']}</b>",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await state.set_state(RegistrationStates.WaitingForGroup)
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n\n"
        "Я бот расписания. Помогу узнать расписание занятий.\n\n"
        "Пожалуйста, введите номер вашей учебной группы\n"
        "(например: <b>РИ-150943А</b>):"
    )


@start_router.message(RegistrationStates.WaitingForGroup)
async def process_group(message: Message, state: FSMContext) -> None:
    group = message.text.strip()
    await state.update_data(primary_group=group)
    await state.set_state(RegistrationStates.WaitingForSubgroups)
    await message.answer(
        f"Группа: <b>{group}</b>\n\n"
        "Теперь укажите подгруппы по предметам.\n"
        "Введите через запятую в формате:\n"
        "<code>Предмет: Подгруппа</code>\n\n"
        "Например: <code>Физика: ЛБ-04, Информатика: ЛБ-01</code>\n\n"
        "Или напишите <b>Нет</b>, если подгрупп нет:"
    )


@start_router.message(RegistrationStates.WaitingForSubgroups)
async def process_subgroups(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    primary_group = data["primary_group"]
    text = message.text.strip()

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

    await create_user(message.from_user.id, primary_group, subgroups)
    await state.clear()

    subgroup_info = ""
    if subgroups:
        lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
        subgroup_info = "\n\nПодгруппы:\n" + "\n".join(lines)

    await message.answer(
        f"Регистрация завершена!\n\n"
        f"Группа: <b>{primary_group}</b>{subgroup_info}\n\n"
        "Используйте кнопки меню для работы с ботом.",
        reply_markup=get_main_menu_keyboard(),
    )
