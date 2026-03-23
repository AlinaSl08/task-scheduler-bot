from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.database import database

def edit_task_keyboard(tg_id: int): #вывод имеющихся задач
    kb = InlineKeyboardBuilder()
    tasks_list = database.get_all_tasks(tg_id)
    for i in range(1, len(tasks_list) + 1):
        kb.button(text=f"{i}", callback_data=f"edit_task_{i}")
    count = len(tasks_list)
    kb.button(text=f"❎ Отменить изменение", callback_data=f"undo_the_change_1")
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()

def task_change_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🖊️ Название", callback_data="edit_name")
    kb.button(text="📅 Дата", callback_data="edit_date")
    kb.button(text="⏱️ Время", callback_data="edit_time")
    kb.button(text="⏰ Период", callback_data="edit_period")
    kb.button(text="🔔 Напоминание", callback_data="edit_notification")
    kb.button(text="⬅️ Назад", callback_data="undo_the_change_2")
    kb.adjust(2, 2, 2)
    return kb.as_markup()