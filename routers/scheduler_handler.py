from aiogram import Router, F, types
from commands.command import DATA_FILE_PATH
from database.db import read_from_file, save_to_file

scheduler_router = Router()



@scheduler_router.callback_query(F.data.startswith("done_"))
async def mark_task_done(callback: types.CallbackQuery):
    task_id = callback.data.split("_")[1]
    user_id = str(callback.from_user.id)
    data = {}
    read_from_file(DATA_FILE_PATH, data)
    task_found = False
    current_task_name = "Задача"  # Значение по умолчанию

    if user_id in data:
        for task in data[user_id]:
            if str(task.get('id')) == task_id:
                task['completed'] = True
                current_task_name = task.get('name', 'Без названия')
                task_found = True
                break

        if task_found:
            save_to_file(DATA_FILE_PATH, data)
            await callback.message.edit_text(f"✅ Задача *{current_task_name}* выполнена!", parse_mode="Markdown")
        else:
            await callback.answer("Ошибка: задача не найдена в списке", show_alert=True)
    await callback.answer()