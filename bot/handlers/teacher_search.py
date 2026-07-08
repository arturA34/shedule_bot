import datetime
import re
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.keyboards import (
    get_main_menu_keyboard,
    get_teacher_search_cancel_keyboard,
    get_teacher_search_retry_keyboard,
    get_teacher_card_keyboard,
    get_teacher_week_navigation_keyboard,
)
from bot.keyboards.inline import (
    get_teacher_today_keyboard,
    get_teacher_tomorrow_keyboard,
)
from bot.services.export_service import (
    build_safe_filename,
    build_schedule_xlsx,
)
from bot.states.teacher_search import TeacherSearchStates
from database.db import (
    search_teachers,
    get_teacher_by_id,
    get_lessons_by_teacher_and_date,
    get_lessons_by_teacher_and_date_range,
)
from bot.services.schedule_service import has_schedule_data_for_date
from bot.utils.formatter import (
    format_lessons_teacher,
    format_week_schedule_teacher,
)

teacher_search_router = Router(name="teacher_search")


def _current_monday() -> datetime.date:
    today = datetime.date.today()
    return today - datetime.timedelta(days=today.weekday())


def _group_lessons_by_date(lessons_list: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for lesson in lessons_list:
        grouped.setdefault(lesson["date"], []).append(lesson)
    return grouped


def looks_like_fio(text: str) -> bool:
    """Проверяет, похож ли ввод на ФИО преподавателя."""
    text = text.strip()
    if text.startswith("/") or len(text) < 3 or len(text) > 100:
        return False
    if not re.search(r'[А-Яа-яЁё]', text):
        return False
    
    # 1. Формат с инициалами: Иванов И.И. или Иванов И. И.
    if re.match(r'^[А-Яа-яЁё\-]+\s+[А-Яа-яЁё]\.\s*[А-Яа-яЁё]\.?$', text):
        return True
    
    # 2. Фамилия отдельно или Фамилия Имя Отчество (1-3 слова с заглавной буквы)
    words = text.split()
    if 1 <= len(words) <= 3:
        if all(w[0].isupper() and w.replace('-', '').isalpha() for w in words if w):
            return True
            
    return False


async def process_teacher_search_logic(text: str, message: Message, state: FSMContext):
    """Общая логика поиска преподавателя по тексту."""
    results = await search_teachers(text)
    
    try:
        await message.delete()
    except Exception:
        pass
        
    state_data = await state.get_data()
    last_msg_id = state_data.get("last_msg_id")
    
    if not results:
        response_text = (
            f"❌ Преподаватель '{text}' не найден.\n\n"
            f"Проверьте правильность ввода (например: Иванов И.И.)"
        )
        keyboard = get_teacher_search_retry_keyboard()
        await state.clear()
        
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
        
        sent = await message.answer(response_text, reply_markup=keyboard)
        await state.update_data(last_msg_id=sent.message_id)
        
    elif len(results) == 1:
        teacher = results[0]
        
        response_text = (
            f"👨‍🏫 Найден преподаватель: {teacher['fio']}\n"
            f"Кафедра: {teacher['department']}\n"
            f"Email: {teacher['email']}\n\n"
            f"Выберите период:"
        )
        keyboard = get_teacher_card_keyboard()
        await state.set_state(TeacherSearchStates.ShowingTeacherCard)
        await state.update_data(teacher_id=teacher['id'], teacher_fio=teacher['fio'])
        
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
                
        sent = await message.answer(response_text, reply_markup=keyboard)
        await state.update_data(last_msg_id=sent.message_id)
        
    else:
        lines = ["🔍 Найдено несколько преподавателей:\n"]
        for i, t in enumerate(results, 1):
            lines.append(f"{i}. {t['fio']} ({t['department']})")
        lines.append("\nВведите номер нужного преподавателя:")
        response_text = "\n".join(lines)
        
        keyboard = get_teacher_search_cancel_keyboard()
        await state.set_state(TeacherSearchStates.WaitingForTeacherSelect)
        await state.update_data(teachers=results)
        
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
                
        sent = await message.answer(response_text, reply_markup=keyboard)
        await state.update_data(last_msg_id=sent.message_id)


@teacher_search_router.callback_query(F.data == "menu:teacher_search")
async def cb_start_teacher_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TeacherSearchStates.WaitingForTeacherSearch)
    try:
        await callback.message.delete()
    except Exception:
        pass
    sent_msg = await callback.message.answer(
        "🔍 Поиск по преподавателю\n\n"
        "Введите ФИО преподавателя (например: Иванов И.И.)\n"
        "или часть ФИО для поиска.",
        reply_markup=get_teacher_search_cancel_keyboard()
    )
    await state.update_data(last_msg_id=sent_msg.message_id)
    await callback.answer()


@teacher_search_router.message(F.text == "👨‍🏫 Поиск по преподавателю")
async def cmd_start_teacher_search(message: Message, state: FSMContext) -> None:
    await state.set_state(TeacherSearchStates.WaitingForTeacherSearch)
    sent_msg = await message.answer(
        "🔍 Поиск по преподавателю\n\n"
        "Введите ФИО преподавателя (например: Иванов И.И.)\n"
        "или часть ФИО для поиска.",
        reply_markup=get_teacher_search_cancel_keyboard()
    )
    await state.update_data(last_msg_id=sent_msg.message_id)


@teacher_search_router.callback_query(F.data == "teacher_search:cancel")
async def cb_cancel_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@teacher_search_router.message(F.text == "❌ Отмена")
async def cmd_cancel_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "<b>Главное меню</b> 📱\n\n"
        "Выберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )


@teacher_search_router.callback_query(F.data == "teacher_search:retry")
async def cb_retry_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TeacherSearchStates.WaitingForTeacherSearch)
    try:
        await callback.message.delete()
    except Exception:
        pass
    sent_msg = await callback.message.answer(
        "🔍 Поиск по преподавателю\n\n"
        "Введите ФИО преподавателя (например: Иванов И.И.)\n"
        "или часть ФИО для поиска.",
        reply_markup=get_teacher_search_cancel_keyboard()
    )
    await state.update_data(last_msg_id=sent_msg.message_id)
    await callback.answer()


@teacher_search_router.message(F.text == "🔄 Попробовать снова")
async def cmd_retry_search(message: Message, state: FSMContext) -> None:
    await state.set_state(TeacherSearchStates.WaitingForTeacherSearch)
    sent_msg = await message.answer(
        "🔍 Поиск по преподавателю\n\n"
        "Введите ФИО преподавателя (например: Иванов И.И.)\n"
        "или часть ФИО для поиска.",
        reply_markup=get_teacher_search_cancel_keyboard()
    )
    await state.update_data(last_msg_id=sent_msg.message_id)


@teacher_search_router.message(TeacherSearchStates.WaitingForTeacherSearch)
async def process_teacher_search_input(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "<b>Главное меню</b> 📱\n\n"
            "Выберите интересующий раздел:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    await process_teacher_search_logic(text, message, state)


@teacher_search_router.message(TeacherSearchStates.WaitingForTeacherSelect)
async def process_teacher_select_input(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "<b>Главное меню</b> 📱\n\n"
            "Выберите интересующий раздел:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    data = await state.get_data()
    teachers = data.get("teachers", [])
    last_msg_id = data.get("last_msg_id")
    
    try:
        await message.delete()
    except Exception:
        pass
        
    if not text.isdigit():
        err_text = f"Пожалуйста, введите корректный номер преподавателя от 1 до {len(teachers)}:"
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
        sent = await message.answer(err_text, reply_markup=get_teacher_search_cancel_keyboard())
        await state.update_data(last_msg_id=sent.message_id)
        return
        
    idx = int(text)
    if idx < 1 or idx > len(teachers):
        err_text = f"Некорректный номер. Пожалуйста, введите номер от 1 до {len(teachers)}:"
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
        sent = await message.answer(err_text, reply_markup=get_teacher_search_cancel_keyboard())
        await state.update_data(last_msg_id=sent.message_id)
        return
        
    teacher = teachers[idx - 1]
    
    response_text = (
        f"👨‍🏫 Найден преподаватель: {teacher['fio']}\n"
        f"Кафедра: {teacher['department']}\n"
        f"Email: {teacher['email']}\n\n"
        f"Выберите период:"
    )
    keyboard = get_teacher_card_keyboard()
    await state.set_state(TeacherSearchStates.ShowingTeacherCard)
    await state.update_data(teacher_id=teacher['id'], teacher_fio=teacher['fio'])
    
    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass
            
    sent = await message.answer(response_text, reply_markup=keyboard)
    await state.update_data(last_msg_id=sent.message_id)


@teacher_search_router.message(StateFilter(None), F.text)
async def process_non_fsm_message(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if looks_like_fio(text):
        await process_teacher_search_logic(text, message, state)


@teacher_search_router.message(TeacherSearchStates.ShowingTeacherCard, F.text == "📅 Расписание сегодня (преп.)")
async def cmd_teacher_today(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    teacher_id = data.get("teacher_id")
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await message.answer("Преподаватель не найден.")
        return
        
    today = datetime.date.today()
    today_str = today.isoformat()
    
    header = f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):"
    monday_str = _current_monday().isoformat()
    
    if not await has_schedule_data_for_date(today):
        text = (
            f"{header}\n\n"
            f"⚠️ Расписание на этот период ещё не загружено.\n\n"
            f"Пожалуйста, обратитесь к администратору или попробуйте позже."
        )
        keyboard = None
    else:
        lessons = await get_lessons_by_teacher_and_date(teacher['fio'], today_str)
        if lessons:
            text = format_lessons_teacher(lessons, header)
            keyboard = get_teacher_today_keyboard(teacher_id, monday_str)
        else:
            text = f"{header}\n\n😴 Пар нет."
            keyboard = None
            
    await message.answer(text, reply_markup=keyboard)


@teacher_search_router.message(TeacherSearchStates.ShowingTeacherCard, F.text == "📆 Расписание завтра (преп.)")
async def cmd_teacher_tomorrow(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    teacher_id = data.get("teacher_id")
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await message.answer("Преподаватель не найден.")
        return
        
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    
    header = f"📅 Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):"
    monday_str = _current_monday().isoformat()
    
    if not await has_schedule_data_for_date(tomorrow):
        text = (
            f"{header}\n\n"
            f"⚠️ Расписание на этот период ещё не загружено.\n\n"
            f"Пожалуйста, обратитесь к администратору или попробуйте позже."
        )
        keyboard = None
    else:
        lessons = await get_lessons_by_teacher_and_date(teacher['fio'], tomorrow_str)
        if lessons:
            text = format_lessons_teacher(lessons, header)
            keyboard = get_teacher_tomorrow_keyboard(teacher_id, monday_str)
        else:
            text = f"{header}\n\n😴 Пар нет."
            keyboard = None
            
    await message.answer(text, reply_markup=keyboard)


@teacher_search_router.message(TeacherSearchStates.ShowingTeacherCard, F.text == "📋 Расписание неделя (преп.)")
async def cmd_teacher_week(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    teacher_id = data.get("teacher_id")
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await message.answer("Преподаватель не найден.")
        return
        
    monday = _current_monday()
    sunday = monday + datetime.timedelta(days=6)
    
    # Fetch schedule range
    lessons_list = await get_lessons_by_teacher_and_date_range(teacher['fio'], monday.isoformat(), sunday.isoformat())
    
    # Group by date
    week_schedule = _group_lessons_by_date(lessons_list)
        
    # Compact week view
    header = f"📋 Расписание на неделю ({monday.strftime('%d.%m')}–{sunday.strftime('%d.%m')}.{monday.year}):"
    text = format_week_schedule_teacher(monday, week_schedule, header)
    
    keyboard = get_teacher_week_navigation_keyboard(teacher_id, monday, None, include_export=bool(lessons_list))
    await message.answer(text, reply_markup=keyboard)


@teacher_search_router.callback_query(F.data.startswith("t_sch:card:"))
async def cb_teacher_card(callback: CallbackQuery, state: FSMContext) -> None:
    teacher_id = int(callback.data.split(":")[2])
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден в базе данных.", show_alert=True)
        return
        
    text = (
        f"👨‍🏫 Найден преподаватель: {teacher['fio']}\n"
        f"Кафедра: {teacher['department']}\n"
        f"Email: {teacher['email']}\n\n"
        f"Выберите период:"
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    keyboard = get_teacher_card_keyboard()
    await state.set_state(TeacherSearchStates.ShowingTeacherCard)
    await state.update_data(teacher_id=teacher['id'], teacher_fio=teacher['fio'])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@teacher_search_router.callback_query(F.data.startswith("t_sch:today:"))
async def cb_teacher_today(callback: CallbackQuery, state: FSMContext) -> None:
    teacher_id = int(callback.data.split(":")[2])
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return
        
    today = datetime.date.today()
    today_str = today.isoformat()
    monday_str = _current_monday().isoformat()
    
    header = f"📅 Расписание на сегодня ({today.strftime('%d.%m.%Y')}):"
    
    if not await has_schedule_data_for_date(today):
        text = (
            f"{header}\n\n"
            f"⚠️ Расписание на этот период ещё не загружено.\n\n"
            f"Пожалуйста, обратитесь к администратору или попробуйте позже."
        )
        keyboard = None
    else:
        lessons = await get_lessons_by_teacher_and_date(teacher['fio'], today_str)
        if lessons:
            text = format_lessons_teacher(lessons, header)
            keyboard = get_teacher_today_keyboard(teacher_id, monday_str)
        else:
            text = f"{header}\n\n😴 Пар нет."
            keyboard = None
            
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@teacher_search_router.callback_query(F.data.startswith("t_sch:tomorrow:"))
async def cb_teacher_tomorrow(callback: CallbackQuery, state: FSMContext) -> None:
    teacher_id = int(callback.data.split(":")[2])
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return
        
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    monday_str = _current_monday().isoformat()
    
    header = f"📅 Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):"
    
    if not await has_schedule_data_for_date(tomorrow):
        text = (
            f"{header}\n\n"
            f"⚠️ Расписание на этот период ещё не загружено.\n\n"
            f"Пожалуйста, обратитесь к администратору или попробуйте позже."
        )
        keyboard = None
    else:
        lessons = await get_lessons_by_teacher_and_date(teacher['fio'], tomorrow_str)
        if lessons:
            text = format_lessons_teacher(lessons, header)
            keyboard = get_teacher_tomorrow_keyboard(teacher_id, monday_str)
        else:
            text = f"{header}\n\n😴 Пар нет."
            keyboard = None
              
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@teacher_search_router.callback_query(F.data.startswith("t_sch:week:"))
async def cb_teacher_week(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    action = parts[2]
    teacher_id = int(parts[3])
    monday_str = parts[4]
    monday = datetime.date.fromisoformat(monday_str)
    
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return
        
    day_index = None
    if action == "day":
        day_index = int(parts[5])
        
    # Fetch schedule range
    sunday = monday + datetime.timedelta(days=6)
    lessons_list = await get_lessons_by_teacher_and_date_range(teacher['fio'], monday.isoformat(), sunday.isoformat())
    
    # Group by date
    week_schedule = _group_lessons_by_date(lessons_list)
    has_week_lessons = bool(lessons_list)
        
    if day_index is None:
        # Compact week view
        header = f"📋 Расписание на неделю ({monday.strftime('%d.%m')}–{sunday.strftime('%d.%m')}.{monday.year}):"
        text = format_week_schedule_teacher(monday, week_schedule, header)
        keyboard = get_teacher_week_navigation_keyboard(teacher_id, monday, None, include_export=has_week_lessons)
    else:
        # Detailed day view
        day = monday + datetime.timedelta(days=day_index)
        lessons = week_schedule.get(day.isoformat(), [])
        
        accusative_weekdays = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]
        day_name = accusative_weekdays[day_index]
        header = f"📋 Расписание на {day_name} ({day.strftime('%d.%m.%Y')}):"
        
        if lessons:
            text = format_lessons_teacher(lessons, header)
        else:
            if day_index in (5, 6):
                text = f"{header}\n\n😴 Пар нет (выходной)"
            else:
                text = f"{header}\n\n😴 Пар нет"
                
        keyboard = get_teacher_week_navigation_keyboard(teacher_id, monday, day_index, include_export=bool(lessons))
        
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@teacher_search_router.callback_query(F.data.startswith("export:teacher:"))
async def cb_export_teacher_schedule(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    export_kind = parts[2]
    teacher_id = int(parts[3])
    teacher = await get_teacher_by_id(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден.", show_alert=True)
        return

    if export_kind == "week":
        monday = datetime.date.fromisoformat(parts[4])
        sunday = monday + datetime.timedelta(days=6)
        lessons = await get_lessons_by_teacher_and_date_range(
            teacher["fio"],
            monday.isoformat(),
            sunday.isoformat(),
        )
        filename = build_safe_filename(
            f"Расписание_преподавателя_{teacher['fio']}_неделя_{monday.strftime('%d.%m.%Y')}-{sunday.strftime('%d.%m.%Y')}",
            "xlsx",
        )
    else:
        if parts[4] == "today":
            target_date = datetime.date.today()
        elif parts[4] == "tomorrow":
            target_date = datetime.date.today() + datetime.timedelta(days=1)
        else:
            monday = datetime.date.fromisoformat(parts[4])
            target_date = monday + datetime.timedelta(days=int(parts[5]))

        lessons = await get_lessons_by_teacher_and_date(teacher["fio"], target_date.isoformat())
        filename = build_safe_filename(
            f"Расписание_преподавателя_{teacher['fio']}_{target_date.strftime('%d.%m.%Y')}",
            "xlsx",
        )

    if not lessons:
        await callback.answer("Для экспорта нет занятий.", show_alert=True)
        return

    document = BufferedInputFile(
        build_schedule_xlsx(lessons, sheet_title="Расписание", view="teacher"),
        filename=filename,
    )
    await callback.message.answer_document(document, caption="Экспорт расписания преподавателя (Excel)")
    await callback.answer("Файл экспорта отправлен.")
