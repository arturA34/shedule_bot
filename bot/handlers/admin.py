import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    AdminGroupSelCb,
    AdminNavCb,
    AdminLessonCb,
    get_admin_groups_keyboard,
    get_admin_schedule_keyboard,
    get_admin_lesson_keyboard,
    get_admin_delete_confirm_keyboard,
    get_admin_lesson_number_keyboard,
    get_admin_lesson_type_keyboard,
    get_admin_subgroup_keyboard,
)
from bot.states.admin import AdminGroupStates, AdminAddLessonStates, AdminEditLessonStates
from database.db import (
    get_all_groups,
    get_lessons_by_group_and_date,
    get_lesson_by_id,
    create_lesson,
    update_lesson_subject,
    update_lesson_room_building,
    update_lesson_teacher,
    delete_lesson,
)
from bot.services.notification_service import notify_users_about_changes

admin_router = Router(name="admin")

WEEKDAY_LABELS = {
    0: "понедельник",
    1: "вторник",
    2: "среду",
    3: "четверг",
    4: "пятницу",
    5: "субботу",
    6: "воскресенье",
}

LESSON_TIMES = {
    1: ("08:30", "10:00"),
    2: ("10:10", "11:40"),
    3: ("11:50", "13:20"),
    4: ("13:30", "15:00"),
    5: ("15:10", "16:40"),
    6: ("16:50", "18:20"),
}


def get_ru_day_of_week(date_str: str) -> str:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        return days[dt.weekday()]
    except Exception:
        return "Понедельник"


async def show_admin_groups_menu(
    message: Message,
    state: FSMContext,
    edit_message_id: int = None,
) -> None:
    await state.clear()
    groups = await get_all_groups()
    text = "<b>Панель администратора</b> 🛠️\n\nВыберите группу для управления расписанием или создайте новую:"
    keyboard = get_admin_groups_keyboard(groups)

    if edit_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=edit_message_id,
                text=text,
                reply_markup=keyboard,
            )
            return
        except Exception:
            pass

    await message.answer(text, reply_markup=keyboard)


async def show_group_schedule(
    message: Message,
    group_name: str,
    date_str: str,
    state: FSMContext,
    edit_message_id: int = None,
) -> None:
    await state.clear()
    lessons = await get_lessons_by_group_and_date(group_name, date_str)

    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday = WEEKDAY_LABELS.get(dt.weekday(), "")
        date_label = f"{dt.strftime('%d.%m.%Y')} ({weekday})"
    except Exception:
        date_label = date_str

    text = f"Управление расписанием группы <b>{group_name}</b> на <b>{date_label}</b>"
    keyboard = get_admin_schedule_keyboard(group_name, date_str, lessons)

    if edit_message_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=edit_message_id,
                text=text,
                reply_markup=keyboard,
            )
            return
        except Exception:
            pass

    await message.answer(text, reply_markup=keyboard)


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await show_admin_groups_menu(message, state)


@admin_router.callback_query(AdminGroupSelCb.filter())
async def cb_admin_group_sel(callback: CallbackQuery, callback_data: AdminGroupSelCb, state: FSMContext) -> None:
    action = callback_data.action
    group_name = callback_data.group_name

    if action == "list":
        await show_admin_groups_menu(callback.message, state, edit_message_id=callback.message.message_id)
    elif action == "select":
        today_str = datetime.date.today().isoformat()
        await show_group_schedule(callback.message, group_name, today_str, state, edit_message_id=callback.message.message_id)
    elif action == "create":
        await state.set_state(AdminGroupStates.WaitingForGroupName)
        sent_msg = await callback.message.edit_text(
            "<b>Создание новой группы</b> ➕\n\n"
            "Пожалуйста, введите название новой группы (например, <b>РИ-150943В</b>):"
        )
        await state.update_data(last_msg_id=sent_msg.message_id)
    await callback.answer()


@admin_router.message(AdminGroupStates.WaitingForGroupName)
async def process_create_group_name(message: Message, state: FSMContext) -> None:
    group_name = message.text.strip()

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    today_str = datetime.date.today().isoformat()
    await show_group_schedule(
        message=message,
        group_name=group_name,
        date_str=today_str,
        state=state,
        edit_message_id=last_msg_id,
    )


@admin_router.callback_query(AdminNavCb.filter())
async def cb_admin_nav(callback: CallbackQuery, callback_data: AdminNavCb, state: FSMContext) -> None:
    action = callback_data.action
    group_name = callback_data.group_name
    date_str = callback_data.date_str

    current_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    if action == "prev":
        new_date = current_date - datetime.timedelta(days=1)
        await show_group_schedule(callback.message, group_name, new_date.isoformat(), state, edit_message_id=callback.message.message_id)
    elif action == "next":
        new_date = current_date + datetime.timedelta(days=1)
        await show_group_schedule(callback.message, group_name, new_date.isoformat(), state, edit_message_id=callback.message.message_id)
    elif action == "current":
        await show_group_schedule(callback.message, group_name, date_str, state, edit_message_id=callback.message.message_id)
    elif action == "view":
        await show_group_schedule(callback.message, group_name, date_str, state, edit_message_id=callback.message.message_id)
    elif action == "add":
        await state.set_state(AdminAddLessonStates.WaitingForLessonNumber)
        await state.update_data(
            group_name=group_name,
            date_str=date_str,
            last_msg_id=callback.message.message_id,
        )
        await callback.message.edit_text(
            f"<b>Добавление пары для {group_name} на {date_str}</b>\n\n"
            "Шаг 1 из 6: Выберите номер пары:",
            reply_markup=get_admin_lesson_number_keyboard(),
        )
    await callback.answer()


@admin_router.callback_query(AdminAddLessonStates.WaitingForLessonNumber, lambda c: c.data and c.data.startswith("lesson_num:"))
async def cb_add_lesson_number(callback: CallbackQuery, state: FSMContext) -> None:
    lesson_num = int(callback.data.split(":", 1)[1])
    times = LESSON_TIMES.get(lesson_num, ("00:00", "00:00"))

    await state.update_data(
        lesson_number=lesson_num,
        start_time=times[0],
        end_time=times[1],
    )
    await state.set_state(AdminAddLessonStates.WaitingForSubject)
    await callback.message.edit_text(
        "Шаг 2 из 6: Введите название предмета (например, Математика):"
    )
    await callback.answer()


@admin_router.message(AdminAddLessonStates.WaitingForSubject)
async def process_add_lesson_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()
    await state.update_data(subject=subject)

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    await state.set_state(AdminAddLessonStates.WaitingForLessonType)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=last_msg_id,
        text="Шаг 3 из 6: Выберите тип занятия:",
        reply_markup=get_admin_lesson_type_keyboard(),
    )


@admin_router.callback_query(AdminAddLessonStates.WaitingForLessonType, lambda c: c.data and c.data.startswith("lesson_type:"))
async def cb_add_lesson_type(callback: CallbackQuery, state: FSMContext) -> None:
    lesson_type = callback.data.split(":", 1)[1]
    await state.update_data(lesson_type=lesson_type)

    await state.set_state(AdminAddLessonStates.WaitingForTeacher)
    await callback.message.edit_text(
        "Шаг 4 из 6: Введите ФИО преподавателя (например, Иванов И.И.):"
    )
    await callback.answer()


@admin_router.message(AdminAddLessonStates.WaitingForTeacher)
async def process_add_lesson_teacher(message: Message, state: FSMContext) -> None:
    teacher = message.text.strip()
    await state.update_data(teacher=teacher)

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    await state.set_state(AdminAddLessonStates.WaitingForRoomAndBuilding)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=last_msg_id,
        text="Шаг 5 из 6: Введите аудиторию и корпус через запятую\n(например: <code>301, Главный</code>):",
    )


@admin_router.message(AdminAddLessonStates.WaitingForRoomAndBuilding)
async def process_add_lesson_room(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    room = text
    building = ""

    if "," in text:
        room, building = text.split(",", 1)
        room = room.strip()
        building = building.strip()

    await state.update_data(room=room, building=building)

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")

    await state.set_state(AdminAddLessonStates.WaitingForSubgroup)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=last_msg_id,
        text="Шаг 6 из 6: Выберите или введите подгруппу (например, ЛБ-01):",
        reply_markup=get_admin_subgroup_keyboard(),
    )


async def save_new_lesson(message: Message, state: FSMContext, subgroup_name: Optional[str]) -> None:
    data = await state.get_data()
    group_name = data["group_name"]
    date_str = data["date_str"]
    last_msg_id = data["last_msg_id"]

    day_of_week = get_ru_day_of_week(date_str)

    await create_lesson(
        day_of_week=day_of_week,
        date_str=date_str,
        lesson_number=data["lesson_number"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        subject=data["subject"],
        teacher=data["teacher"],
        room=data["room"],
        building=data["building"],
        lesson_type=data["lesson_type"],
        group_name=group_name,
        subgroup_name=subgroup_name,
    )

    await show_group_schedule(
        message=message,
        group_name=group_name,
        date_str=date_str,
        state=state,
        edit_message_id=last_msg_id,
    )


@admin_router.callback_query(AdminAddLessonStates.WaitingForSubgroup, F.data == "lesson_subgroup:all")
async def cb_add_lesson_subgroup_all(callback: CallbackQuery, state: FSMContext) -> None:
    await save_new_lesson(callback.message, state, subgroup_name=None)
    await callback.answer()


@admin_router.message(AdminAddLessonStates.WaitingForSubgroup)
async def process_add_lesson_subgroup_text(message: Message, state: FSMContext) -> None:
    subgroup = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass
    await save_new_lesson(message, state, subgroup_name=subgroup)


@admin_router.callback_query(AdminLessonCb.filter(F.action == "view"))
async def cb_view_lesson(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    lesson = await get_lesson_by_id(callback_data.lesson_id)
    if not lesson:
        await callback.answer("Пара не найдена.", show_alert=True)
        return

    sub = f" (Подгруппа: {lesson['subgroup_name']})" if lesson.get("subgroup_name") else " (Для всей группы)"
    text = (
        f"<b>Детали пары №{lesson['lesson_number']}</b>\n\n"
        f"Группа: <b>{lesson['group_name']}</b>\n"
        f"Дата: <b>{lesson['date']} ({lesson['day_of_week']})</b>\n"
        f"Время: <b>{lesson['start_time']} - {lesson['end_time']}</b>\n"
        f"Предмет: <b>{lesson['subject']}</b> ({lesson['lesson_type']})\n"
        f"Преподаватель: <b>{lesson['teacher'] or '—'}</b>\n"
        f"Аудитория: <b>{lesson['room'] or '—'}</b> (корп. <b>{lesson['building'] or '—'}</b>)\n"
        f"Состав: <b>{sub}</b>"
    )

    keyboard = get_admin_lesson_keyboard(lesson["id"], lesson["date"], lesson["group_name"])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_router.callback_query(AdminLessonCb.filter(F.action == "edit_subject"))
async def cb_edit_lesson_subject(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    await state.set_state(AdminEditLessonStates.WaitingForEditSubject)
    await state.update_data(
        lesson_id=callback_data.lesson_id,
        group_name=callback_data.group_name,
        date_str=callback_data.date_str,
        last_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text("Введите новое название предмета:")
    await callback.answer()


@admin_router.message(AdminEditLessonStates.WaitingForEditSubject)
async def process_edit_subject(message: Message, state: FSMContext) -> None:
    new_subject = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    lesson_id = data["lesson_id"]
    last_msg_id = data["last_msg_id"]
    group_name = data["group_name"]
    date_str = data["date_str"]

    old_lesson = await get_lesson_by_id(lesson_id)
    if old_lesson:
        await update_lesson_subject(lesson_id, new_subject)
        new_lesson = await get_lesson_by_id(lesson_id)

        diff_fields = {"subject": (old_lesson["subject"], new_subject)}
        changes = {
            "added": [],
            "deleted": [],
            "changed": [
                {
                    "old": old_lesson,
                    "new": new_lesson,
                    "diff": diff_fields,
                }
            ]
        }
        await notify_users_about_changes(changes)

    await show_group_schedule(message, group_name, date_str, state, edit_message_id=last_msg_id)


@admin_router.callback_query(AdminLessonCb.filter(F.action == "edit_room"))
async def cb_edit_lesson_room(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    await state.set_state(AdminEditLessonStates.WaitingForEditRoom)
    await state.update_data(
        lesson_id=callback_data.lesson_id,
        group_name=callback_data.group_name,
        date_str=callback_data.date_str,
        last_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        "Введите новую аудиторию и корпус через запятую\n(например: <code>210, Корпус Б</code>):"
    )
    await callback.answer()


@admin_router.message(AdminEditLessonStates.WaitingForEditRoom)
async def process_edit_room(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    lesson_id = data["lesson_id"]
    last_msg_id = data["last_msg_id"]
    group_name = data["group_name"]
    date_str = data["date_str"]

    room = text
    building = ""
    if "," in text:
        room, building = text.split(",", 1)
        room = room.strip()
        building = building.strip()

    old_lesson = await get_lesson_by_id(lesson_id)
    if old_lesson:
        await update_lesson_room_building(lesson_id, room, building)
        new_lesson = await get_lesson_by_id(lesson_id)

        diff_fields = {}
        if old_lesson["room"] != room:
            diff_fields["room"] = (old_lesson["room"], room)
        if old_lesson["building"] != building:
            diff_fields["building"] = (old_lesson["building"], building)

        if diff_fields:
            changes = {
                "added": [],
                "deleted": [],
                "changed": [
                    {
                        "old": old_lesson,
                        "new": new_lesson,
                        "diff": diff_fields,
                    }
                ]
            }
            await notify_users_about_changes(changes)

    await show_group_schedule(message, group_name, date_str, state, edit_message_id=last_msg_id)


@admin_router.callback_query(AdminLessonCb.filter(F.action == "edit_teacher"))
async def cb_edit_lesson_teacher(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    await state.set_state(AdminEditLessonStates.WaitingForEditTeacher)
    await state.update_data(
        lesson_id=callback_data.lesson_id,
        group_name=callback_data.group_name,
        date_str=callback_data.date_str,
        last_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text("Введите ФИО нового преподавателя:")
    await callback.answer()


@admin_router.message(AdminEditLessonStates.WaitingForEditTeacher)
async def process_edit_teacher(message: Message, state: FSMContext) -> None:
    new_teacher = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    lesson_id = data["lesson_id"]
    last_msg_id = data["last_msg_id"]
    group_name = data["group_name"]
    date_str = data["date_str"]

    old_lesson = await get_lesson_by_id(lesson_id)
    if old_lesson:
        await update_lesson_teacher(lesson_id, new_teacher)
        new_lesson = await get_lesson_by_id(lesson_id)

        diff_fields = {"teacher": (old_lesson["teacher"], new_teacher)}
        changes = {
            "added": [],
            "deleted": [],
            "changed": [
                {
                    "old": old_lesson,
                    "new": new_lesson,
                    "diff": diff_fields,
                }
            ]
        }
        await notify_users_about_changes(changes)

    await show_group_schedule(message, group_name, date_str, state, edit_message_id=last_msg_id)


@admin_router.callback_query(AdminLessonCb.filter(F.action == "delete"))
async def cb_delete_lesson_confirm(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    lesson_id = callback_data.lesson_id
    date_str = callback_data.date_str
    group_name = callback_data.group_name

    lesson = await get_lesson_by_id(lesson_id)
    if not lesson:
        await callback.answer("Пара не найдена.", show_alert=True)
        return

    text = (
        f"❓ <b>Вы уверены, что хотите удалить эту пару?</b>\n\n"
        f"Предмет: <b>{lesson['subject']}</b>\n"
        f"Группа: <b>{group_name}</b>\n"
        f"Дата: <b>{date_str}</b>\n"
        f"Пара №{lesson['lesson_number']}"
    )
    keyboard = get_admin_delete_confirm_keyboard(lesson_id, date_str, group_name)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_router.callback_query(AdminLessonCb.filter(F.action == "confirm_delete"))
async def cb_delete_lesson_execute(callback: CallbackQuery, callback_data: AdminLessonCb, state: FSMContext) -> None:
    lesson_id = callback_data.lesson_id
    date_str = callback_data.date_str
    group_name = callback_data.group_name

    old_lesson = await get_lesson_by_id(lesson_id)
    if old_lesson:
        await delete_lesson(lesson_id)

        changes = {
            "added": [],
            "deleted": [old_lesson],
            "changed": []
        }
        await notify_users_about_changes(changes)

    await callback.answer("Пара успешно удалена.", show_alert=True)
    await show_group_schedule(callback.message, group_name, date_str, state, edit_message_id=callback.message.message_id)
