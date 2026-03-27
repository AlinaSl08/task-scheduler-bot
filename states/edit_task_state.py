from aiogram.fsm.state import StatesGroup, State

class EditTask(StatesGroup):
    name = State()
    date = State()
    time = State()
    period = State()
    notification = State()