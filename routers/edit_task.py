from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F, Bot
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.main_kb import main_menu_keyboard
from keyboards.edit_task_kb import edit_task_keyboard, task_change_keyboard
from routers.output_task import output_task
from states.edit_task_state import EditTask
from keyboards.add_task_kb import get_date_keyboard, get_period_keyboard, get_notification_keyboard, get_time_hour_keyboard
from routers.add_task import convert_selected_days_to_str
from _datetime import datetime
from states.menu_state import Menu
from database.database import database
from utils.scheduler import schedule_all_tasks, add_overdue_checker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

edit_task_router = Router()

#делаем клавиатуру состоящую из всех уже сохраненных задач(кол-во кнопок зависит от этого)
@edit_task_router.callback_query(F.data == "change")
async def edit_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    if len(tasks_list) == 0:
        await call.message.answer("😊 Нет задач, которые можно изменить")
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
        await call.answer()
    else:
        tasks_list_out = output_task(tasks_list, cap="1")
        tasks_message = await call.message.answer(tasks_list_out)
        await state.update_data(tasks_message_id=tasks_message.message_id)
        await call.message.answer(f"Выберите задачу, которую желаете изменить:",
                                  reply_markup=edit_task_keyboard(user_id))
        await call.answer()

#отмена изменения
@edit_task_router.callback_query(F.data.startswith("undo_the_change_"))
async def undo_the_change(call: CallbackQuery, state: FSMContext):
    mode_edit = int(call.data.split("_")[3])
    await safe_delete(call.message)
    data = await state.get_data()
    if mode_edit == 1: #отменить изменение
        tasks_last_message_id = data.get("tasks_message_id")
    else: #вернуться назад
        tasks_last_message_id = data.get("tasks_list_id")
    await delete_last_message(tasks_last_message_id, call.message)
    await call.answer("Изменение отменено!")
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg = await call.message.answer("Выберите действие:",
                                        reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

#что именно меняем
@edit_task_router.callback_query(F.data.startswith("edit_task_"))
async def edit_number_task(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    number_task = int(call.data.split("_")[2]) #номер задачи + 1
    data = await state.get_data()
    tasks_last_message_id = data.get("tasks_message_id")
    await state.update_data(number_task=number_task)
    await delete_last_message(tasks_last_message_id, call.message)
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    tasks_list_out = output_task(tasks_list, cap="1", str_task=number_task)
    tasks_list_id_out = await call.message.answer(f"Вы выбрали задачу номер {number_task}:\n\n{tasks_list_out}")
    await state.update_data(task=tasks_list[number_task - 1], tasks_list_id=tasks_list_id_out.message_id)
    await call.message.answer("Что именно в задаче вы желаете изменить?", reply_markup=task_change_keyboard())

#изменить дату
@edit_task_router.callback_query(F.data == "edit_date")
async def edit_date(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    #сегодняшняя дата
    current_datetime = datetime.now()
    current_month = current_datetime.month
    current_year = current_datetime.year
    #текущее число (сегодня) для проверки на прошедшие даты
    real_current_day = current_datetime.day
    real_current_month = current_datetime.month
    real_current_year = current_datetime.year
    await state.update_data(current_month=current_month, current_year=current_year, real_current_month=real_current_month,
                            real_current_year=real_current_year, real_current_day=real_current_day)
    bot_msg = await call.message.answer("Выберите новую дату для вашей задачи:",
                                        reply_markup=get_date_keyboard(current_month=current_month,
                                                                  current_year=current_year, mode_key=2))
    await state.update_data(bot_msg_id=bot_msg.message_id)
    await state.set_state(EditTask.date)

#изменить название
@edit_task_router.callback_query(F.data == "edit_name")
async def edit_name(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    bot_msg = await call.message.answer("Напишите название задачи:")
    await state.update_data(bot_msg=bot_msg.message_id)
    await state.set_state(EditTask.name)

@edit_task_router.message(EditTask.name)
async def get_new_name(message: Message,  state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    new_name = message.text
    data = await state.get_data()
    bot_last_msg = data.get("bot_msg")
    task_id = (data.get("task"))[0]
    tasks_message_id_out = data.get("tasks_list_id")
    await delete_last_message(tasks_message_id_out, message)
    await delete_last_message(bot_last_msg, message)
    database.edit_name_task(task_id, new_name)
    scheduler.remove_all_jobs()
    schedule_all_tasks(scheduler, bot)
    add_overdue_checker(scheduler)
    await message.answer("✅ Название задачи успешно изменено!")
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg = await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

#изменить время
@edit_task_router.callback_query(F.data == "edit_time")
async def edit_time(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    current_datetime = datetime.now().date()
    await state.update_data(current_datetime=current_datetime)
    bot_msg = await call.message.answer("Выберите время для вашей задачи:",
                                        reply_markup=get_time_hour_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=bot_msg.message_id)
    await state.set_state(EditTask.time)

#изменить период
@edit_task_router.callback_query(F.data == "edit_period")
async def edit_period(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    selected = [0, 0, 0, 0, 0, 0, 0]
    await state.update_data(selected_days=selected)
    bot_msg = await call.message.answer("Выберите новый период для вашей задачи:",
                                        reply_markup=get_period_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=bot_msg.message_id)
    await state.set_state(EditTask.period)

@edit_task_router.callback_query(F.data == "continue_get_period_edit")
async def continue_get_period_edit(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    data = await state.get_data()
    period = convert_selected_days_to_str(data["selected_days"])
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    number_task = data.get("number_task")
    task_id = database.get_all_tasks(user_id)[number_task - 1][0]
    database.delete_old_period_task(task_id) #удаляются все записи периода об этой задачи
    for day in period:
        day_id = database.get_weekday_id(day)
        database.save_period_task(task_id, day_id) #сохраняем период заново
    scheduler.remove_all_jobs()
    schedule_all_tasks(scheduler, bot)
    add_overdue_checker(scheduler)
    await call.message.answer("✅ Период повторения задачи изменен!")
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg_id = data.get("bot_msg_id")
    tasks_message_id_out = data.get("tasks_list_id")
    await delete_last_message(tasks_message_id_out, call.message)
    await delete_last_message(bot_msg_id, call.message)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

@edit_task_router.callback_query(F.data == "no_period_edit")
async def no_period_edit(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    await call.message.answer("✅ Задача изменена! Повторяться не будет!")
    data = await state.get_data()
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    number_task = data.get("number_task")
    task_id = database.get_all_tasks(user_id)[number_task - 1][0]
    database.delete_old_period_task(task_id)
    scheduler.remove_all_jobs()
    schedule_all_tasks(scheduler, bot)
    add_overdue_checker(scheduler)
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg_id = data.get("bot_msg_id")
    tasks_message_id_out = data.get("tasks_list_id")
    await delete_last_message(tasks_message_id_out, call.message)
    await delete_last_message(bot_msg_id, call.message)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

#изменить напоминание
@edit_task_router.callback_query(F.data == "edit_notification")
async def edit_notification(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    bot_msg = await call.message.answer("Выберите напоминание для вашей задачи:",
                                        reply_markup=get_notification_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=bot_msg.message_id)
    await state.set_state(EditTask.notification)

#Если пользователь пишет текстом, а не выбирает кнопки в клавиатуре
@edit_task_router.message(EditTask.date)
async def ignore_input_date(message: Message, state: FSMContext):
    data = await state.get_data()
    old_bot_msg_id = data.get("bot_msg_id")
    if old_bot_msg_id:
        await delete_last_message(old_bot_msg_id, message)
    current_datetime = datetime.now()
    current_month = current_datetime.month
    current_year = current_datetime.year
    new_bot_msg = await message.answer("Пожалуйста, выберите дату с помощью кнопок ниже 👇",
                                       reply_markup=get_date_keyboard(current_month=current_month,
                                                                      current_year=current_year, mode_key=2))
    await state.update_data(bot_msg_id=new_bot_msg.message_id)

@edit_task_router.message(EditTask.period)
async def ignore_input_period(message: Message, state: FSMContext):
    data = await state.get_data()
    old_bot_msg_id = data.get("bot_msg_id")
    # удаляем старое сообщение, если оно есть
    if old_bot_msg_id:
        await delete_last_message(old_bot_msg_id, message)
    new_bot_msg = await message.answer("Пожалуйста, выберите период с помощью кнопок ниже 👇",
                                       reply_markup=get_period_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=new_bot_msg.message_id)

@edit_task_router.message(EditTask.notification)
async def ignore_input_notification(message: Message, state: FSMContext):
    data = await state.get_data()
    old_bot_msg_id = data.get("bot_msg_id")
    # удаляем старое сообщение, если оно есть
    if old_bot_msg_id:
        await delete_last_message(old_bot_msg_id, message)
    new_bot_msg = await message.answer("Пожалуйста, выберите напоминание с помощью кнопок ниже 👇",
                                       reply_markup=get_period_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=new_bot_msg.message_id)

@edit_task_router.message(EditTask.time)
async def ignore_input_time(message: Message, state: FSMContext):
    data = await state.get_data()
    old_bot_msg_id = data.get("bot_msg_id")
    if old_bot_msg_id:
        await delete_last_message(old_bot_msg_id, message)
    new_bot_msg = await message.answer("Пожалуйста, выберите время с помощью кнопок ниже 👇",
                                       reply_markup=get_time_hour_keyboard(mode_key=2))
    await state.update_data(bot_msg_id=new_bot_msg.message_id)