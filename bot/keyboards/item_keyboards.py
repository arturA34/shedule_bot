from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_items_main_menu() -> InlineKeyboardMarkup:
    """Главное меню управления предметами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить предмет", callback_data="item_add"),
                InlineKeyboardButton(text="✏️ Редактировать предмет", callback_data="item_edit"),
            ],
            [
                InlineKeyboardButton(text="🗑️ Удалить предмет", callback_data="item_delete"),
                InlineKeyboardButton(text="📋 Посмотреть все предметы", callback_data="item_list_all"),
            ],
            [
                InlineKeyboardButton(text="🔄 Сменить основную группу", callback_data="item_change_group"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="item_back"),
            ]
        ]
    )


def get_subgroup_choice(item_name: str, main_group: str) -> InlineKeyboardMarkup:
    """Выбор подгруппы при добавлении/редактировании"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📌 Основная группа ({main_group})",
                    callback_data=f"item_set_main_{item_name}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Ввести вручную",
                    callback_data=f"item_manual_{item_name}"
                ),
            ]
        ]
    )


def get_available_subgroups(subgroups: list, item_name: str) -> InlineKeyboardMarkup:
    """Список доступных подгрупп"""
    buttons = []
    for subgroup in subgroups:
        buttons.append([
            InlineKeyboardButton(
                text=subgroup,
                callback_data=f"item_subgroup_{item_name}_{subgroup}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="📌 Основная группа",
            callback_data=f"item_set_main_{item_name}"
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            text="✏️ Ввести вручную",
            callback_data=f"item_manual_{item_name}"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_items_list(items: list, action: str) -> InlineKeyboardMarkup:
    """Список предметов для выбора (редактирование/удаление)"""
    buttons = []
    for item in items:
        # Используем subject или name
        name = item.get('subject') or item.get('name', 'Без названия')
        subgroup = item.get('subgroup', 'Основная группа')
        buttons.append([
            InlineKeyboardButton(
                text=f"{name} → {subgroup}",
                callback_data=f"{action}_{name}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="item_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_continue_keyboard() -> InlineKeyboardMarkup:
    """После добавления"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить ещё", callback_data="item_add_more"),
                InlineKeyboardButton(text="🔙 Вернуться в управление", callback_data="item_back"),
            ]
        ]
    )


def get_edit_continue() -> InlineKeyboardMarkup:
    """После редактирования"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать ещё", callback_data="item_edit_again"),
                InlineKeyboardButton(text="🔙 Вернуться в управление", callback_data="item_back"),
            ]
        ]
    )


def get_delete_continue() -> InlineKeyboardMarkup:
    """После удаления"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Удалить ещё", callback_data="item_delete_again"),
                InlineKeyboardButton(text="🔙 Вернуться в управление", callback_data="item_back"),
            ]
        ]
    )


def get_confirm_delete(item_name: str) -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"item_confirm_delete_{item_name}"),
                InlineKeyboardButton(text="❌ Нет, отмена", callback_data="item_back"),
            ]
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="item_back"),
            ]
        ]
    )


def get_all_items_keyboard() -> InlineKeyboardMarkup:
    """Список всех предметов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="item_back"),
            ]
        ]
    )