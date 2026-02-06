from aiogram.types import CallbackQuery
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import tasks
from keyboards.clear_task_kb import confirm_clear_keyboard

clear_task_router = Router()

@clear_task_router.callback_query(F.data == "clear")
async def clear_task(call: CallbackQuery):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    if len(tasks[tg_id]) == 0:
        await call.message.answer("🙁 Список уже пуст!")
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()
    else:
        await call.message.answer("⚠️ Вы уверены, что хотите удалить ВСЕ задачи?", reply_markup=confirm_clear_keyboard())
        await call.answer()

# очистить список
@clear_task_router.callback_query(F.data == "clear_yes")
async def confirm_clear(call: CallbackQuery):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    tasks[tg_id].clear()
    await call.message.answer("🗑️ Все задачи удалены")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

# очистка списка отменена
@clear_task_router.callback_query(F.data == "clear_no")
async def cancel_clear(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("❎ Очистка отменена")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()