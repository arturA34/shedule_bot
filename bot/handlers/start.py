import json

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import get_main_menu_keyboard
from bot.states.registration import RegistrationStates
from database.db import get_user, create_user, verify_and_claim_invite
from bot.handlers.change_group import parse_subgroup_input, update_subgroups_message

start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
    args = command.args
    if args and args.startswith("admin_"):
        token = args.replace("admin_", "", 1)
        success = await verify_and_claim_invite(token, message.from_user.id)
        if success:
            await message.answer(
                "Вы успешно авторизованы как администратор. Теперь вам доступна команда /admin."
            )
            return
        else:
            await message.answer(
                "❌ Ссылка для авторизации администратора недействительна или уже была использована."
            )

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
        "(например: <b>РИ-150943</b>):"
    )
    await state.update_data(last_msg_id=sent_msg.message_id)


@start_router.message(RegistrationStates.WaitingForGroup)
async def process_group(message: Message, state: FSMContext) -> None:
    group = message.text.strip()
    await state.update_data(primary_group=group, subgroups=[])
    
    # Delete the user's input message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass
    # Clear last_msg_id so update_subgroups_message generates a new one
    await state.update_data(last_msg_id=None)

    await state.set_state(RegistrationStates.WaitingForSubgroups)
    await update_subgroups_message(message, state, group, [], is_registration=True)


@start_router.message(RegistrationStates.WaitingForSubgroups)
async def process_subgroups(message: Message, state: FSMContext) -> None:
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
        # Save user in DB
        await create_user(message.from_user.id, primary_group, subgroups)
        
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
            subgroup_info = "\n\nВаши подгруппы:\n" + "\n".join(lines)
        else:
            subgroup_info = "\n\nПодгруппы: не указаны."

        success_text = (
            f"Регистрация успешно завершена! 🎉\n\n"
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
            message, state, primary_group, subgroups, error_text=error_text, is_registration=True
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
    await update_subgroups_message(message, state, primary_group, subgroups, is_registration=True)
