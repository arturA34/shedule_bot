import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_week_navigation_keyboard, get_back_keyboard
from bot.services.schedule_service import (
    UserNotRegisteredError,
    get_user_schedule,
    get_user_schedule_range,
    has_schedule_data_for_date,
)
from bot.states.registration import RegistrationStates
from bot.utils.formatter import format_schedule

schedule_router = Router(name="schedule")

WEEKDAY_LABELS = {
    0: "понедельник",
    1: "вторник",
    2: "среду",
    3: "четверг",
    4: "пятницу",
    5: "субботу",
    6: "воскресенье",
}


def _date_label(d: datetime.date) -> str:
    weekday = WEEKDAY_LABELS.get(d.weekday(), "")
    return f"{d.strftime('%d.%m.%Y')} ({weekday})"


def _week_bounds() -> tuple[datetime.date, datetime.date]:
    """Возвращает (понедельник, воскресенье) текущей недели."""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday


async def show_today_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    today = datetime.date.today()

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

    if lessons:
        text = format_schedule(lessons, _date_label(today))
    elif not await has_schedule_data_for_date(today):
        text = "Расписание на эту дату ещё не загружено."
    else:
        text = "На сегодня занятий нет."

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=get_back_keyboard())
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=get_back_keyboard())


async def show_tomorrow_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

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

    if lessons:
        text = format_schedule(lessons, _date_label(tomorrow))
    elif not await has_schedule_data_for_date(tomorrow):
        text = "Расписание на эту дату ещё не загружено."
    else:
        text = "На завтра занятий нет."

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=get_back_keyboard())
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=get_back_keyboard())


async def show_week_schedule(
    chat_id: int,
    user_id: int,
    state: FSMContext,
    day_index_override: int = None,
    monday_override: datetime.date = None,
    message_to_edit: Message = None,
    message_to_reply: Message = None,
) -> None:
    if monday_override:
        monday = monday_override
    else:
        monday, sunday = _week_bounds()

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

    if day_index_override is not None:
        day_index = day_index_override
    else:
        # Ищем первый день с занятиями
        for i in range(7):
            day = monday + datetime.timedelta(days=i)
            if week_schedule.get(day.isoformat()):
                day_index = i
                break
        else:
            text = "На этой неделе занятий нет."
            if message_to_edit:
                try:
                    await message_to_edit.edit_text(text, reply_markup=get_back_keyboard())
                    return
                except Exception:
                    pass
            await (message_to_reply or message_to_edit).answer(text, reply_markup=get_back_keyboard())
            return

    day = monday + datetime.timedelta(days=day_index)
    lessons = week_schedule.get(day.isoformat(), [])

    text = format_schedule(lessons, _date_label(day))
    if not lessons:
        text = f"<b>{_date_label(day)}</b>\n\nВ этот день занятий нет."

    has_prev = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index))
    has_next = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index + 1, 7))

    keyboard = get_week_navigation_keyboard(monday, day_index, has_prev, has_next)

    if message_to_edit:
        try:
            await message_to_edit.edit_text(text, reply_markup=keyboard)
            return
        except Exception:
            pass

    await (message_to_reply or message_to_edit).answer(text, reply_markup=keyboard)


@schedule_router.message(Command("today"))
async def cmd_today(message: Message, state: FSMContext) -> None:
    await show_today_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@schedule_router.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message, state: FSMContext) -> None:
    await show_tomorrow_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
        message_to_reply=message,
    )


@schedule_router.message(Command("week"))
async def cmd_week(message: Message, state: FSMContext) -> None:
    await show_week_schedule(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        state=state,
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
    await show_week_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        message_to_edit=callback.message,
    )
    await callback.answer()


@schedule_router.callback_query(lambda c: c.data and c.data.startswith("week:"))
async def cb_week_nav(callback: CallbackQuery, state: FSMContext) -> None:
    _, monday_str, day_index_str = callback.data.split(":", 2)
    monday = datetime.date.fromisoformat(monday_str)
    day_index = int(day_index_str)

    await show_week_schedule(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        state=state,
        day_index_override=day_index,
        monday_override=monday,
        message_to_edit=callback.message,
    )
    await callback.answer()

