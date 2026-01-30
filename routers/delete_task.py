from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import tasks
from keyboards.delete_task_kb import delete_task_keyboard, delete_issue
from routers.output_task import output_task

delete_task_router = Router()

#делаем клавиатуру состоящую из всех уже сохраненных задач(кол-во кнопок зависит от этого)
@delete_task_router.callback_query(F.data == "delete")
async def delete_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    if len(tasks[tg_id]) == 0:
        await call.message.answer("😊 Нет задач, которые можно удалить")
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()
    else:
        tasks_list = output_task(tg_id)
        tasks_message = await call.message.answer(tasks_list)
        await state.update_data(tasks_message_id=tasks_message.message_id)
        await call.message.answer(f"Выберите задачу, которую желаете удалить:", reply_markup=delete_task_keyboard(tg_id))
        await call.answer()

@delete_task_router.callback_query(F.data.startswith("del_task_"))
async def delete(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number_task = int(call.data.split("_")[2])
    await state.update_data(number_task=number_task)
    await call.message.answer("⚠️ Вы уверены, что хотите выполнить удаление?", reply_markup=delete_issue())
    await call.answer()

@delete_task_router.callback_query(F.data == "delete_no")
async def delete_no(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    await call.bot.delete_message(chat_id=call.message.chat.id,
                message_id=tasks_message)
    await call.message.answer("❎ Удаление отменено")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

@delete_task_router.callback_query(F.data == "delete_yes")
async def delete_yes(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    await call.bot.delete_message(chat_id=call.message.chat.id,
                                  message_id=tasks_message)
    number_task = data.get("number_task")
    tg_id = call.from_user.id
    del tasks[tg_id][number_task - 1]
    await call.message.answer("✅ Задача успешно удалена!")
    print(tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()