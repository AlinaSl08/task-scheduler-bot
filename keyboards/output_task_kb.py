from aiogram.utils.keyboard import InlineKeyboardBuilder
from storage.tasks import tasks

def completed_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Отметить выполненные задачи", callback_data="mark_completed")
    kb.button(text="⬅️ Вернуться в меню", callback_data="menu")
    kb.adjust(1, 1)
    return kb.as_markup()


def completed_task_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    for i in range(1, len(tasks[tg_id]) + 1):
        if tasks[tg_id][i - 1]["completed"]:
            kb.button(text=f"✅ {i}", callback_data=f"completed_task_{i}")
        else:
            kb.button(text=f"{i}", callback_data=f"completed_task_{i}")
    kb.button(text=f"Вернуться в меню", callback_data=f"menu")
    count = len(tasks[tg_id])
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()