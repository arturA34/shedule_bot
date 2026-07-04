import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.schedule_service import (
    UserNotRegisteredError,
    get_user_schedule,
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
