from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.database import database

scheduler_router = Router()

@scheduler_router.callback_query(F.data.startswith("done_"))
async def mark_task_done(call: CallbackQuery):
    task_id = int(call.data.split("_")[1])
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    task_found = False
    current_task_name = "Задача"  # Значение по умолчанию
    if user_id: #если такой юзер есть
        for task in tasks_list:
            if task[0] == task_id:
                database.edit_is_status_task(task_id, 1)
                current_task_name = task[1]
                task_found = True
                break
        if task_found:
            await call.message.edit_text(f"✅ Задача *{current_task_name}* выполнена!", parse_mode="Markdown")
            await call.answer()
        else:
            await call.answer("Ошибка: задача не найдена в списке", show_alert=True)