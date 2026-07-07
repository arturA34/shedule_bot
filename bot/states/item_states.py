from aiogram.fsm.state import State, StatesGroup


class ItemStates(StatesGroup):
    """Состояния для управления подгруппами"""
    waiting_for_item_name = State()      # Ожидание названия предмета
    waiting_for_subgroup = State()       # Ожидание ввода подгруппы
    waiting_for_new_group = State()      # Ожидание новой группы при смене