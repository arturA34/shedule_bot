from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    WaitingForGroup = State()
    WaitingForSubgroups = State()


class ChangeGroupStates(StatesGroup):
    WaitingForGroup = State()


class ChangeSubgroupsStates(StatesGroup):
    WaitingForSubgroups = State()


