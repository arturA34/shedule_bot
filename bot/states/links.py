from aiogram.fsm.state import State, StatesGroup


class LinkStates(StatesGroup):
    """Состояния для управления ссылками."""
    WaitingForURL = State()
    WaitingForTitle = State()
    WaitingForDelete = State()