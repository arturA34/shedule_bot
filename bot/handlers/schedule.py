import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import get_week_navigation_keyboard
from bot.services.schedule_service import (
    UserNotRegisteredError,
    get_user_schedule,
    get_user_schedule_range,
    has_schedule_data_for_date,
)
from bot.states.registration import RegistrationStates
from bot.utils.formatter import (
    format_lessons_student,
    format_week_schedule_student,
)

schedule_router = Router(name="schedule")


def pluralize_lessons(n: int) -> str:
    """Возвращает число и склоненную форму слова 'пара' (например, '1 пара', '3 пары', '5 пар')."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} пара"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} пары"
    else:
        return f"{n} пар"


async def show_today_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    try:
        lessons = await get_user_schedule(user_id, today)
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        text = "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы (например: <b>РИ-150943А</b>):"
        if message_to_edit:
            try:
                await message_to_edit.edit_text(text)
                await state.update_data(last_msg_id=message_to_edit.message_id)
                return
            except Exception:
                pass
        sent_msg = await (message_to_reply or message_to_edit).answer(text)
        await state.update_data(last_msg_id=sent_msg.message_id)
        return

    # Check if there are lessons today
    if lessons:
        header = f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):"
        text = format_lessons_student(lessons, header)
    else:
        # Check if schedule data exists for today
        if not await has_schedule_data_for_date(today):
            text = (
                f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
                f"⚠️ Расписание на этот период ещё не загружено.\n\n"
                f"Пожалуйста, обратитесь к администратору или попробуйте позже."
            )
        else:
            # Holiday today
            try:
                lessons_tomorrow = await get_user_schedule(user_id, tomorrow)
            except Exception:
                lessons_tomorrow = []
            
            tomorrow_count = len(lessons_tomorrow)
            tomorrow_date_str = tomorrow.strftime('%d.%m.%Y')
            lessons_word = pluralize_lessons(tomorrow_count)
            text = (
                f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
                f"😴 Пар нет. Можете отдохнуть или подготовиться к следующим занятиям.\n\n"
                f"Завтра ({tomorrow_date_str}) у вас запланировано {lessons_word}."
            )

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=None)
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=None)


async def show_tomorrow_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    today = datetime.date.today()

    try:
        lessons = await get_user_schedule(user_id, tomorrow)
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        text = "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы (например: <b>РИ-150943А</b>):"
        if message_to_edit:
            try:
                await message_to_edit.edit_text(text)
                await state.update_data(last_msg_id=message_to_edit.message_id)
                return
            except Exception:
                pass
        sent_msg = await (message_to_reply or message_to_edit).answer(text)
        await state.update_data(last_msg_id=sent_msg.message_id)
        return

    # Check if there are lessons tomorrow
    if lessons:
        header = f"📅 Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):"
        text = format_lessons_student(lessons, header)
    else:
        # Check if schedule data exists for tomorrow
        if not await has_schedule_data_for_date(tomorrow):
            text = (
                f"📅 Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):\n\n"
                f"⚠️ Расписание на этот период ещё не загружено.\n\n"
                f"Пожалуйста, обратитесь к администратору или попробуйте позже."
            )
        else:
            # Holiday tomorrow
            try:
                lessons_today = await get_user_schedule(user_id, today)
            except Exception:
                lessons_today = []
            
            today_count = len(lessons_today)
            today_date_str = today.strftime('%d.%m.%Y')
            lessons_word = pluralize_lessons(today_count)
            text = (
                f"📅 Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):\n\n"
                f"😴 Завтра пар нет. Хорошего выходного!\n\n"
                f"Сегодня ({today_date_str}) у вас было {lessons_word}."
            )

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=None)
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=None)


async def show_week_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    monday: datetime.date,
    day_index: Optional[int] = None,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    try:
        week_schedule = await get_user_schedule_range(user_id, monday, monday + datetime.timedelta(days=6))
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        text = "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы (например: <b>РИ-150943А</b>):"
        if message_to_edit:
            try:
                await message_to_edit.edit_text(text)
                await state.update_data(last_msg_id=message_to_edit.message_id)
                return
            except Exception:
                pass
        sent_msg = await (message_to_reply or message_to_edit).answer(text)
        await state.update_data(last_msg_id=sent_msg.message_id)
        return

    if day_index is None:
        # Compact week view
        sunday = monday + datetime.timedelta(days=6)
        header = f"📋 Расписание на неделю ({monday.strftime('%d.%m')}–{sunday.strftime('%d.%m')}.{monday.year}):"
        text = format_week_schedule_student(monday, week_schedule, header)
        keyboard = get_week_navigation_keyboard(monday, None)
    else:
        # Detailed day view
        day = monday + datetime.timedelta(days=day_index)
        lessons = week_schedule.get(day.isoformat(), [])
        
        accusative_weekdays = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]
        day_name = accusative_weekdays[day_index]
        header = f"📋 Расписание на {day_name} ({day.strftime('%d.%m.%Y')}):"
        
        if lessons:
            text = format_lessons_student(lessons, header)
        else:
            if day_index in (5, 6):
                text = f"{header}\n\n😴 Пар нет (выходной)"
            else:
                text = f"{header}\n\n😴 Пар нет"
                
        keyboard = get_week_navigation_keyboard(monday, day_index)

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=keyboard)
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=keyboard)


@schedule_router.message(Command("today"))
@schedule_router.message(F.text == "📅 Расписание на сегодня")
async def cmd_today(message: Message, state: FSMContext) -> None:
    await show_today_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@schedule_router.message(Command("tomorrow"))
@schedule_router.message(F.text == "📆 Расписание на завтра")
async def cmd_tomorrow(message: Message, state: FSMContext) -> None:
    await show_tomorrow_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@schedule_router.message(Command("week"))
@schedule_router.message(F.text == "📋 Расписание на неделю")
async def cmd_week(message: Message, state: FSMContext) -> None:
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    await show_week_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        monday=monday,
        day_index=None,
        message_to_reply=message,
    )


@schedule_router.callback_query(F.data == "menu:today")
async def cb_today(callback: CallbackQuery, state: FSMContext) -> None:
    await show_today_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        message_to_edit=callback.message,
    )
    await callback.answer()


@schedule_router.callback_query(F.data == "menu:tomorrow")
async def cb_tomorrow(callback: CallbackQuery, state: FSMContext) -> None:
    await show_tomorrow_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        message_to_edit=callback.message,
    )
    await callback.answer()


@schedule_router.callback_query(F.data == "menu:week")
async def cb_week(callback: CallbackQuery, state: FSMContext) -> None:
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    await show_week_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        monday=monday,
        day_index=None,
        message_to_edit=callback.message,
    )
    await callback.answer()


@schedule_router.callback_query(F.data.startswith("week:"))
async def cb_week_navigation(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    # Expected formats:
    # week:show:YYYY-MM-DD
    # week:day:YYYY-MM-DD:day_index
    action = parts[1]
    monday_str = parts[2]
    monday = datetime.date.fromisoformat(monday_str)
    
    day_index = None
    if action == "day":
        day_index = int(parts[3])
        
    await show_week_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        monday=monday,
        day_index=day_index,
        message_to_edit=callback.message,
    )
    await callback.answer()
