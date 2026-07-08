from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
import datetime
from bot.keyboards.reply import get_main_menu_keyboard
from bot.states.item_states import ItemStates
from bot.keyboards.item_keyboards import *
from bot.services.export_service import build_safe_filename, build_subjects_xlsx
from bot.services.item_service import ItemService

router = Router(name="items")


async def show_management_menu(message: Message):
    """Показать главное меню управления предметами"""
    user_id = message.from_user.id
    
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await message.answer("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    items = await ItemService.get_user_items(user_id)
    
    text = f"🔧 Управление предметами\n\n"
    text += f"Основная группа: {main_group}\n\n"
    text += f"Все предметы ({len(items)}):\n"
    
    if items:
        for item in items:
            subject = item.get('subject') or item.get('name', '')
            subgroup = item.get('subgroup', 'Основная группа')
            is_main = "Основная группа" in subgroup
            status = "✅" if not is_main else ""
            text += f" {status} {subject} → {subgroup}\n"
    else:
        text += " 📭 Нет добавленных предметов\n"
    
    await message.answer(text, reply_markup=get_items_main_menu())


@router.callback_query(F.data == "item_list_all")
async def show_all_subjects(callback: CallbackQuery):
    """Показать все предметы из расписания"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    subjects = await ItemService.get_all_subjects()
    text = f"📋 Список всех предметов в расписании ({len(subjects)}):\n\n"
    if subjects:
        for i, subject in enumerate(subjects, 1):
            text += f"{i}. {subject}\n"
        keyboard = get_all_items_keyboard()
    else:
        text += "📭 В расписании пока нет предметов.\n"
        keyboard = get_back_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "item_export_all")
async def export_all_subjects(callback: CallbackQuery):
    subjects = await ItemService.get_all_subjects()
    if not subjects:
        await callback.answer("Для экспорта нет предметов.", show_alert=True)
        return

    document = BufferedInputFile(
        build_subjects_xlsx(subjects, sheet_title="Предметы"),
        filename=build_safe_filename(
            f"Список_всех_предметов_{datetime.date.today().strftime('%d.%m.%Y')}",
            "xlsx",
        ),
    )
    await callback.message.answer_document(document, caption="Экспорт списка предметов (Excel)")
    await callback.answer("Файл экспорта отправлен.")


@router.callback_query(F.data == "item_add")
async def start_add_item(callback: CallbackQuery, state: FSMContext):
    """Начать добавление предмета"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    await state.set_state(ItemStates.waiting_for_item_name)
    try:
        await callback.message.edit_text("Введите название предмета:", reply_markup=get_back_keyboard())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_back_keyboard())


@router.message(ItemStates.waiting_for_item_name)
async def process_item_name(message: Message, state: FSMContext):
    """Обработка названия предмета при добавлении"""
    subject = message.text.strip()
    user_id = message.from_user.id
    
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await message.answer("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    if not await ItemService.subject_exists(subject):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Посмотреть все предметы", callback_data="item_list_all")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="item_back")]
            ]
        )
        await message.answer(
            f"❌ Предмет '{subject}' не найден в расписании.\n\nВозможно, вы ошиблись в названии.",
            reply_markup=keyboard
        )
        return
    
    items = await ItemService.get_user_items(user_id)
    for item in items:
        if item.get('subject', '').lower() == subject.lower() or item.get('name', '').lower() == subject.lower():
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"item_edit_select_{subject}"),
                        InlineKeyboardButton(text="❌ Отмена", callback_data="item_back")
                    ]
                ]
            )
            await message.answer(
                f"⚠️ Предмет '{subject}' уже добавлен с подгруппой '{item.get('subgroup', 'Основная группа')}'.\nХотите изменить?",
                reply_markup=keyboard
            )
            await state.clear()
            return
    
    await state.update_data(item_name=subject)
    await message.answer(
        f"✅ Предмет '{subject}' найден.\n\nВыберите подгруппу:",
        reply_markup=get_subgroup_choice(subject, main_group)
    )
    await state.set_state(ItemStates.waiting_for_subgroup)


@router.callback_query(F.data.startswith("item_set_main_"))
async def set_main_subgroup(callback: CallbackQuery, state: FSMContext):
    """Установить основную группу для предмета"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    subject = callback.data.replace("item_set_main_", "")
    subgroup = f"Основная группа ({main_group})"
    await ItemService.add_item(user_id, subject, subgroup)
    
    text = f"✅ Предмет '{subject}' добавлен с основной группой."
    try:
        await callback.message.edit_text(text, reply_markup=get_continue_keyboard())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_continue_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("item_manual_"))
async def manual_subgroup_input(callback: CallbackQuery, state: FSMContext):
    """Ввести подгруппу вручную"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    subject = callback.data.replace("item_manual_", "")
    await state.update_data(item_name=subject)
    available = await ItemService.get_available_subgroups(subject, main_group)
    
    if available:
        text = f"Доступные подгруппы для '{subject}':\n{', '.join(available)}\n\nВыберите подгруппу или введите вручную:"
        try:
            await callback.message.edit_text(text, reply_markup=get_available_subgroups(available, subject))
        except Exception:
            await callback.message.edit_reply_markup(reply_markup=get_available_subgroups(available, subject))
    else:
        text = f"Введите вашу подгруппу по предмету '{subject}':"
        try:
            await callback.message.edit_text(text, reply_markup=get_back_keyboard())
        except Exception:
            await callback.message.edit_reply_markup(reply_markup=get_back_keyboard())
    await state.set_state(ItemStates.waiting_for_subgroup)


@router.callback_query(F.data.startswith("item_subgroup_"))
async def select_subgroup_from_list(callback: CallbackQuery, state: FSMContext):
    """Выбрать подгруппу из списка"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    parts = callback.data.split("_")
    subject = parts[2]
    subgroup = "_".join(parts[3:])
    await ItemService.add_item(user_id, subject, subgroup)
    
    text = f"✅ Подгруппа по предмету '{subject}' установлена: {subgroup}"
    try:
        await callback.message.edit_text(text, reply_markup=get_continue_keyboard())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_continue_keyboard())
    await state.clear()


@router.message(ItemStates.waiting_for_subgroup)
async def process_manual_subgroup(message: Message, state: FSMContext):
    """Обработка ручного ввода подгруппы"""
    subgroup = message.text.strip()
    data = await state.get_data()
    subject = data.get('item_name')
    user_id = message.from_user.id
    
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await message.answer("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    available = await ItemService.get_available_subgroups(subject, main_group)
    
    if available and subgroup not in available:
        await message.answer(
            f"❌ Подгруппа '{subgroup}' не найдена для предмета '{subject}' в группе {main_group}.\n\nДоступные подгруппы: {', '.join(available)}",
            reply_markup=get_available_subgroups(available, subject)
        )
        return
    
    await ItemService.add_item(user_id, subject, subgroup)
    await message.answer(
        f"✅ Подгруппа по предмету '{subject}' установлена: {subgroup}",
        reply_markup=get_continue_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "item_add_more")
async def add_more_item(callback: CallbackQuery, state: FSMContext):
    """Добавить ещё предмет"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    await state.set_state(ItemStates.waiting_for_item_name)
    try:
        await callback.message.edit_text("Введите название предмета:", reply_markup=get_back_keyboard())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_back_keyboard())


@router.callback_query(F.data == "item_edit")
async def start_edit_item(callback: CallbackQuery):
    """Начать редактирование предмета"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    items = await ItemService.get_user_items(user_id)
    if not items:
        await callback.message.edit_text("📭 У вас нет добавленных предметов.", reply_markup=get_back_keyboard())
        return
    
    try:
        await callback.message.edit_text("Выберите предмет для редактирования:", reply_markup=get_items_list(items, "item_edit_select"))
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_items_list(items, "item_edit_select"))


@router.callback_query(F.data.startswith("item_edit_select_"))
async def select_item_to_edit(callback: CallbackQuery, state: FSMContext):
    """Выбор предмета для редактирования"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    subject = callback.data.replace("item_edit_select_", "")
    items = await ItemService.get_user_items(user_id)
    current_item = None
    for item in items:
        if item.get('subject', '').lower() == subject.lower() or item.get('name', '').lower() == subject.lower():
            current_item = item
            break
    if not current_item:
        await callback.message.edit_text("❌ Предмет не найден.")
        return
    await state.update_data(item_name=subject)
    text = f"✏️ Редактирование: {subject}\nТекущая подгруппа: {current_item.get('subgroup', 'Основная группа')}\n\nВыберите новую подгруппу:"
    try:
        await callback.message.edit_text(text, reply_markup=get_subgroup_choice(subject, main_group))
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_subgroup_choice(subject, main_group))
    await state.set_state(ItemStates.waiting_for_subgroup)


@router.callback_query(F.data == "item_edit_again")
async def edit_again(callback: CallbackQuery):
    """Редактировать ещё предмет"""
    await callback.answer()
    await start_edit_item(callback)


@router.callback_query(F.data == "item_delete")
async def start_delete_item(callback: CallbackQuery):
    """Начать удаление предмета"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    items = await ItemService.get_user_items(user_id)
    if not items:
        await callback.message.edit_text("📭 У вас нет добавленных предметов.", reply_markup=get_back_keyboard())
        return
    
    try:
        await callback.message.edit_text("Выберите предмет для удаления:", reply_markup=get_items_list(items, "item_delete_select"))
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_items_list(items, "item_delete_select"))


@router.callback_query(F.data.startswith("item_delete_select_"))
async def confirm_delete_item(callback: CallbackQuery):
    """Подтверждение удаления"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    subject = callback.data.replace("item_delete_select_", "")
    text = f"⚠️ Вы уверены, что хотите удалить подгруппу по предмету '{subject}'?\n\nПредмет будет удалён из вашего списка.\nПодгруппа вернётся на 'Основная группа'."
    try:
        await callback.message.edit_text(text, reply_markup=get_confirm_delete(subject))
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_confirm_delete(subject))


@router.callback_query(F.data.startswith("item_confirm_delete_"))
async def delete_item(callback: CallbackQuery):
    """Удалить предмет"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    subject = callback.data.replace("item_confirm_delete_", "")
    await ItemService.delete_item(user_id, subject)
    
    text = f"🗑️ Подгруппа по предмету '{subject}' удалена."
    try:
        await callback.message.edit_text(text, reply_markup=get_delete_continue())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_delete_continue())


@router.callback_query(F.data == "item_delete_again")
async def delete_again(callback: CallbackQuery):
    """Удалить ещё предмет"""
    await callback.answer()
    await start_delete_item(callback)


@router.callback_query(F.data == "item_change_group")
async def start_change_group(callback: CallbackQuery, state: FSMContext):
    """Начать смену основной группы"""
    await callback.answer()
    
    user_id = callback.from_user.id
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await callback.message.edit_text("⚠️ Вы не зарегистрированы! Введите /start")
        return
    
    await state.set_state(ItemStates.waiting_for_new_group)
    text = ("🔄 Смена основной группы\n\n"
            "⚠️ Внимание! При смене группы:\n"
            "• Все ваши подгруппы будут удалены\n"
            "• Автоматически загрузятся предметы из расписания новой группы\n"
            "• Вам нужно будет заново указать отличающиеся подгруппы\n\n"
            "Введите новую основную группу:")
    try:
        await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=get_back_keyboard())


@router.message(ItemStates.waiting_for_new_group)
async def process_change_group(message: Message, state: FSMContext):
    """Обработка смены группы"""
    new_group = message.text.strip().upper()
    user_id = message.from_user.id
    
    main_group = await ItemService.get_user_main_group(user_id)
    if not main_group:
        await message.answer("⚠️ Вы не зарегистрированы! Введите /start")
        await state.clear()
        return
    
    if not await ItemService.group_exists(new_group):
        all_groups = await ItemService.get_all_groups()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="item_change_group")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="item_back")]
            ]
        )
        await message.answer(
            f"❌ Группа '{new_group}' не найдена в расписании.\n\nДоступные группы: {', '.join(all_groups[:5])}...\nВведите корректную группу:",
            reply_markup=keyboard
        )
        return
    
    subgroups = await ItemService.change_group(user_id, new_group)
    
    text = "⏳ Обновляю данные...\n\n"
    text += f"🔄 Выполнено:\n"
    text += f" ✅ Основная группа обновлена: {main_group} → {new_group}\n"
    text += f" 🗑️ Удалены все старые подгруппы\n"
    text += f" 📚 Загружены предметы из расписания новой группы ({len(subgroups)}):\n"
    for item in subgroups[:15]:
        text += f"    • {item.get('subject', item.get('name', ''))} → {item.get('subgroup', 'Основная группа')}\n"
    if len(subgroups) > 15:
        text += f"    ... и ещё {len(subgroups) - 15} предметов\n"
    text += f"\n⚠️ Важно! Теперь укажите предметы, по которым ваша группа отличается от новой.\nВведите название предмета (или 'Готово', если всё верно):"
    
    await message.answer(text)
    await state.clear()
    await state.set_state(ItemStates.waiting_for_item_name)


@router.callback_query(F.data == "item_back")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await callback.answer()
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "<b>Главное меню</b> 📱\n\nВыберите интересующий раздел:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "menu:settings")
async def handle_settings_callback(callback: CallbackQuery):
    """Обработчик кнопки из инлайн-меню"""
    await callback.answer()
    await show_management_menu(callback.message)