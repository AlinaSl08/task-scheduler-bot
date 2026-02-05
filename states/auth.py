from aiogram.fsm.state import StatesGroup, State

class Auth(StatesGroup):
    timezone = State()