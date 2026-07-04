from aiogram.fsm.state import State, StatesGroup


class AdminGroupStates(StatesGroup):
    WaitingForGroupName = State()


class AdminAddLessonStates(StatesGroup):
    WaitingForLessonNumber = State()
    WaitingForSubject = State()
    WaitingForLessonType = State()
    WaitingForTeacher = State()
    WaitingForRoomAndBuilding = State()
    WaitingForSubgroup = State()


class AdminEditLessonStates(StatesGroup):
    WaitingForEditSubject = State()
    WaitingForEditRoom = State()
    WaitingForEditTeacher = State()
