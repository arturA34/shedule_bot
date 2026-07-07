from aiogram import Router

from bot.handlers.start import start_router
from bot.handlers.menu import menu_router
from bot.handlers.schedule import schedule_router
from bot.handlers.admin import admin_router
from bot.handlers.help import help_router
from bot.handlers.change_group import change_group_router
from bot.handlers.teacher_search import teacher_search_router
from bot.handlers.item_handlers import router as items_router

all_routers = [
    start_router,
    menu_router,
    schedule_router,
    admin_router,
    help_router,
    change_group_router,
    teacher_search_router,
    items_router,
]

__all__ = ["all_routers"]

