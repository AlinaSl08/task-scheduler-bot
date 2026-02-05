from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from main.utils import safe_delete
from main.keyboards.main_kb import main_menu_keyboard
from main.storage import tasks
from main.keyboards.edit_task_kb import edit_task_keyboard, task_change_keyboard
from main.routers.output_task import output_task

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
    await state.update_data(number_task=number_task)
    await call.message.answer("Что именно в задаче вы желаете изменить?", reply_markup=task_change_keyboard())
    await call.answer()

#изменение (тут доделать само изменение)
@edit_task_router.callback_query(F.data == "edit_name")
async def edit(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    await call.bot.delete_message(chat_id=call.message.chat.id,
                                  message_id=tasks_message)
    number_task = data.get("number_task") #номер задачи
    tg_id = call.from_user.id
    bot_msg = await call.message.answer("Напишите название задачи:")
    #new_name = get_new_name(bot_msg)
    #tasks[tg_id][number_task - 1]['name'] = new_name
    await call.message.answer("✅ Название задачи успешно изменено!")
    print(tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

'''
class EditTask(StatesGroup):
    name = State()
    date = State()
    time = State()
    period = State()
    notification = State()

@main_router.message(EditTask.name)
async def get_new_name(message: Message):
    name = message.text
    return name
'''