from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.filters import StateFilter
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import tasks
from keyboards.edit_task_kb import edit_task_keyboard, task_change_keyboard
from routers.output_task import output_task
from states.edit_task import EditTask
from database.db import save_to_file
from commands.command import DATA_FILE_PATH
from keyboards.add_task_kb import get_date_keyboard
from _datetime import datetime

edit_task_router = Router()

#делаем клавиатуру состоящую из всех уже сохраненных задач(кол-во кнопок зависит от этого)
@edit_task_router.callback_query(F.data == "change")
async def edit_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    if len(tasks[tg_id]) == 0:
        await call.message.answer("😊 Нет задач, которые можно изменить")
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()
    else:
        tasks_list = output_task(tg_id, cap="1")
        tasks_message = await call.message.answer(tasks_list)
        await state.update_data(tasks_message_id=tasks_message.message_id)
        await call.message.answer(f"Выберите задачу, которую желаете изменить:",
                                  reply_markup=edit_task_keyboard(tg_id))
        await call.answer()

#отмена изменения
@edit_task_router.callback_query(F.data == "undo_the_change")
async def undo_the_change(call: CallbackQuery):
    await safe_delete(call.message)
    await call.answer("Изменение отменено!")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

#что именно меняем
@edit_task_router.callback_query(F.data.startswith("edit_task_"))
async def edit_number_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number_task = int(call.data.split("_")[2])
    data = await state.get_data()
    tasks_last_message_id = data.get("tasks_message_id")
    await state.update_data(number_task=number_task)
    await delete_last_message(tasks_last_message_id, call.message)
    tg_id = call.from_user.id
    tasks_list = output_task(tg_id, cap="1", str_task=number_task)
    await call.message.answer(f"Вы выбрали задачу номер {number_task}:\n\n{tasks_list}")
    await call.message.answer("Что именно в задаче вы желаете изменить?", reply_markup=task_change_keyboard())
    await call.answer()

#изменение (тут доделать само изменение)
@edit_task_router.callback_query(F.data == "edit_name")
async def edit_name(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    #await call.bot.delete_message(chat_id=call.message.chat.id,
    #                              message_id=tasks_message)
    bot_msg = await call.message.answer("Напишите название задачи:")
    await state.update_data(bot_msg=bot_msg.message_id)
    await state.set_state(EditTask.name)

@edit_task_router.callback_query(F.data == "edit_date")
async def edit_date(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    current_datetime = datetime.now()
    current_month = current_datetime.month
    current_year = current_datetime.year
    real_current_day = current_datetime.day
    real_current_month = current_datetime.month
    real_current_year = current_datetime.year

    await state.update_data(current_month=current_month, current_year=current_year, real_current_month=real_current_month,
                            real_current_year=real_current_year, real_current_day=real_current_day)
    bot_msg = await call.message.answer("Выберите новую дату для вашей задачи:", reply_markup=get_date_keyboard(current_month=current_month,
                                                                  current_year=current_year, mode_key=2))




#сделать текст вы выбрали вот эту задачу


#изменить название
@edit_task_router.message(EditTask.name)
async def get_new_name(message: Message,  state: FSMContext):
    new_name = message.text
    tg_id = message.from_user.id
    data = await state.get_data()
    number_task = data.get("number_task") #номер задачи
    bot_last_msg = data.get("bot_msg")
    await delete_last_message(bot_last_msg, message)
    tasks[tg_id][number_task - 1]['name'] = new_name
    await message.answer("✅ Название задачи успешно изменено!")
    save_to_file(DATA_FILE_PATH, tasks)
    print(tasks)
    await state.clear()
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

#изменить дату
@edit_task_router.callback_query(StateFilter(EditTask.date)) #вот это не работает
async def edit_date(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()