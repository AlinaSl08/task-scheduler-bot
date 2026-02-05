from aiogram.fsm.state import StatesGroup, State

class AddTask(StatesGroup):
    name = State()
    date = State()
    time = State()
    period = State()
    notification = State()