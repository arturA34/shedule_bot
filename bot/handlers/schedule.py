import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import WEEKDAY_SHORT, get_week_navigation_keyboard
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


@schedule_router.message(Command("today"))
@schedule_router.message(lambda m: m.text == "Расписание на сегодня")
async def cmd_today(message: Message, state: FSMContext) -> None:
    today = datetime.date.today()

    try:
        lessons = await get_user_schedule(message.from_user.id, today)
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        await message.answer(
            "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы:"
        )
        return

    if lessons:
        await message.answer(format_schedule(lessons, _date_label(today)))
        return

    if not await has_schedule_data_for_date(today):
        await message.answer("Расписание на эту дату ещё не загружено.")
        return

    await message.answer("На сегодня занятий нет.")


@schedule_router.message(Command("tomorrow"))
@schedule_router.message(lambda m: m.text == "Расписание на завтра")
async def cmd_tomorrow(message: Message, state: FSMContext) -> None:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    try:
        lessons = await get_user_schedule(message.from_user.id, tomorrow)
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        await message.answer(
            "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы:"
        )
        return

    if lessons:
        await message.answer(format_schedule(lessons, _date_label(tomorrow)))
        return

    if not await has_schedule_data_for_date(tomorrow):
        await message.answer("Расписание на эту дату ещё не загружено.")
        return

    await message.answer("На завтра занятий нет.")


@schedule_router.message(Command("week"))
@schedule_router.message(lambda m: m.text == "Расписание на неделю")
async def cmd_week(message: Message, state: FSMContext) -> None:
    monday, sunday = _week_bounds()

    try:
        week_schedule = await get_user_schedule_range(
            message.from_user.id, monday, sunday
        )
    except UserNotRegisteredError:
        await state.set_state(RegistrationStates.WaitingForGroup)
        await message.answer(
            "Вы не зарегистрированы. Пожалуйста, введите номер вашей учебной группы:"
        )
        return

    # Ищем первый день с занятиями
    for i in range(7):
        day = monday + datetime.timedelta(days=i)
        if week_schedule.get(day.isoformat()):
            day_index = i
            break
    else:
        await message.answer("На этой неделе занятий нет.")
        return

    lessons = week_schedule[day.isoformat()]
    text = format_schedule(lessons, _date_label(day))

    has_prev = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index))
    has_next = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index + 1, 7))

    keyboard = get_week_navigation_keyboard(monday, day_index, has_prev, has_next)
    await message.answer(text, reply_markup=keyboard)


@schedule_router.callback_query(lambda c: c.data and c.data.startswith("week:"))
async def cb_week_nav(callback: CallbackQuery, state: FSMContext) -> None:
    _, monday_str, day_index_str = callback.data.split(":", 2)
    monday = datetime.date.fromisoformat(monday_str)
    day_index = int(day_index_str)

    try:
        week_schedule = await get_user_schedule_range(
            callback.from_user.id, monday, monday + datetime.timedelta(days=6)
        )
    except UserNotRegisteredError:
        await callback.answer("Вы не зарегистрированы.", show_alert=True)
        return

    day = monday + datetime.timedelta(days=day_index)
    lessons = week_schedule.get(day.isoformat(), [])

    if not lessons:
        await callback.answer("В этот день занятий нет.", show_alert=True)
        return

    text = format_schedule(lessons, _date_label(day))

    has_prev = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index))
    has_next = any(week_schedule.get((monday + datetime.timedelta(days=j)).isoformat()) for j in range(day_index + 1, 7))

    keyboard = get_week_navigation_keyboard(monday, day_index, has_prev, has_next)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
