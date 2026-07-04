from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.registration import ChangeGroupStates
from database.db import update_user

change_group_router = Router(name="change_group")


@change_group_router.message(Command("settings"))
@change_group_router.message(Command("change_group"))
@change_group_router.message(F.text == "Сменить группу")
async def cmd_change_group(message: Message, state: FSMContext) -> None:
    await state.set_state(ChangeGroupStates.WaitingForGroup)
    await message.answer(
        "Пожалуйста, введите номер вашей новой учебной группы\n"
        "(например: <b>РИ-150943А</b>):"
    )


@change_group_router.message(ChangeGroupStates.WaitingForGroup)
async def process_change_group(message: Message, state: FSMContext) -> None:
    group = message.text.strip()
    await state.update_data(primary_group=group)
    await state.set_state(ChangeGroupStates.WaitingForSubgroups)
    await message.answer(
        f"Новая группа: <b>{group}</b>\n\n"
        "Теперь укажите подгруппы по предметам.\n"
        "Введите через запятую в формате:\n"
        "<code>Предмет: Подгруппа</code>\n\n"
        "Например: <code>Физика: ЛБ-04, Информатика: ЛБ-01</code>\n\n"
        "Или напишите <b>Нет</b>, если подгрупп нет:"
    )


@change_group_router.message(ChangeGroupStates.WaitingForSubgroups)
async def process_change_subgroups(message: Message, state: FSMContext) -> None:
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

    await update_user(message.from_user.id, primary_group, subgroups)
    await state.clear()

    subgroup_info = ""
    if subgroups:
        lines = [f"  • {s['subject']}: <b>{s['subgroup']}</b>" for s in subgroups]
        subgroup_info = "\n\nНовые подгруппы:\n" + "\n".join(lines)

    await message.answer(
        f"Данные успешно обновлены!\n\n"
        f"Группа: <b>{primary_group}</b>{subgroup_info}\n\n"
        "Используйте кнопки меню для работы с ботом.",
        reply_markup=get_main_menu_keyboard(),
    )
