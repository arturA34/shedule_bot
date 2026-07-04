from aiogram import Router

from bot.handlers.start import start_router
from bot.handlers.menu import menu_router
from bot.handlers.schedule import schedule_router
from bot.handlers.admin import admin_router
from bot.handlers.help import help_router
from bot.handlers.change_group import change_group_router

all_routers = [start_router, menu_router, schedule_router, admin_router, help_router, change_group_router]

__all__ = ["all_routers"]

