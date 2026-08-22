from aiogram.fsm.state import State, StatesGroup


class CheckinStates(StatesGroup):
    stress_level = State()
    energy_level = State()
    plan_done = State()
    blocker_present = State()
    learning_done = State()
    answering = State()


class AuthStates(StatesGroup):
    waiting_email = State()
    waiting_password = State()
