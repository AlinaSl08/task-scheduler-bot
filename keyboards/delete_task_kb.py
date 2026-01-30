from aiogram.utils.keyboard import InlineKeyboardBuilder
from storage.tasks import tasks

def delete_task_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    for i in range(1, len(tasks[tg_id]) + 1):
        kb.button(text=f"{i}", callback_data=f"del_task_{i}")
    count = len(tasks[tg_id])
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()

def delete_issue():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="delete_yes")
    kb.button(text="❌ Нет", callback_data="delete_no")
    kb.adjust(2)
    return kb.as_markup()