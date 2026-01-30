from aiogram.utils.keyboard import InlineKeyboardBuilder
from storage.tasks import tasks

def edit_task_keyboard(tg_id: int): #вывод имеющихся задач
    kb = InlineKeyboardBuilder()
    for i in range(1, len(tasks[tg_id]) + 1):
        kb.button(text=f"{i}", callback_data=f"edit_task_{i}")
    count = len(tasks[tg_id])
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()

def task_change_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Название", callback_data="edit_name")
    kb.button(text="Дата", callback_data="edit_date")
    kb.button(text="Время", callback_data="edit_time")
    kb.button(text="Период", callback_data="edit_period")
    kb.button(text="Напоминание", callback_data="edit_notification")
    kb.button(text="Назад", callback_data="undo_the_change")
    kb.adjust(2, 2, 2)
    return kb.as_markup()