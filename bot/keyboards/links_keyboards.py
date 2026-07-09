from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_links_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню ссылок."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить ссылку", callback_data="links:add"),
                InlineKeyboardButton(text="🗑️ Удалить ссылку", callback_data="links:delete"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="links:back"),
            ]
        ]
    )


def get_links_delete_keyboard(links: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком ссылок для удаления."""
    buttons = []
    for link in links:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑️ {link['title']}",
                callback_data=f"links:delete_confirm:{link['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="links:main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="links:cancel"),
            ]
        ]
    )