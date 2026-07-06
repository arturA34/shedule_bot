from aiogram.fsm.state import State, StatesGroup


class TeacherSearchStates(StatesGroup):
    WaitingForTeacherSearch = State()
    WaitingForTeacherSelect = State()
    ShowingTeacherCard = State()
