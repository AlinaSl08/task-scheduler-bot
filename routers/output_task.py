from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from aiogram import Router, F
from keyboards.output_task_kb import completed_keyboard, completed_task_keyboard
import datetime
from database.database import database
import logging

output_task_router = Router()

#вывод по порядку
def output_task(tasks_list, cap="0", str_task=0):
    # если дата уже прошла и не выполнена, то ставим просрочено(надо сделать)
    tasks_list_out = ["📌 Список дел:"]
    for idx, task in enumerate(tasks_list, 1):
        name = task[1].capitalize()
        date = f"{task[2]:%d.%m.%Y}"
        td = task[3]
        hours = td.seconds // 3600
        minutes = (td.seconds // 60) % 60
        time = f"{hours:02}:{minutes:02}"
        notification_id = task[4]
        completed = ""
        if task[5]: #если True
            completed = " ✅"
        task_id = task[0]
        weekdays_list = database.output_period_task(task_id) #отдельно достаем период
        periods_list = [database.get_weekday(day) for day in weekdays_list]
        if isinstance(periods_list, list):
            period_str = ", ".join(periods_list) if periods_list else "Без повторений"
        else:
            period_str = "Не определен"
        if notification_id == 2:
            notification =  'Напоминать за 10 минут.'
        elif notification_id == 3:
            notification =  'Напоминать за 30 минут.'
        elif notification_id == 4:
            notification = 'Напоминать за 1 час.'
        elif notification_id == 5:
            notification = 'Напоминать за 2 часа.'
        else:
            notification = 'Без напоминаний'
        if cap == "1": #с напоминаниями вывод
            task_text = (f'{idx}){completed} {name} - '
                             f'{date} в {time}. Период повторения: {period_str}. {notification}')
        else: #без напоминаний вывод
                task_text = (f'{idx}){completed} {name} - '
                             f'{date} в {time}. Период повторения: {period_str}')
        tasks_list_out.append(task_text)
    if str_task == 0:
        full_message = '\n\n'.join(tasks_list_out)
        return full_message
    else:
        return tasks_list_out[str_task][3:]

def output_task_week(tasks_list): #тут будет вывод на неделю
    # если дата уже прошла и не выполнена, то ставим просрочено(надо сделать)
    tasks_list_out = []
    indexes = []
    for idx, task in enumerate(tasks_list):
        current_date = datetime.date.today()  # сегодняшняя дата
        days_till_monday = datetime.date.weekday(current_date)
        date_monday = current_date - datetime.timedelta(days=days_till_monday) #дата понедельника с начала недели
        date_sunday = current_date - datetime.timedelta(days=days_till_monday) + datetime.timedelta(days=6)
        if date_sunday >= task[2] >= date_monday:
            indexes.append(idx)
            weekdays = []
            periods = database.output_period_task(task[0])
            for period in periods:
                weekdays.append(database.get_weekday(period))
            completed = task[5]
            td = task[3]
            hours = td.seconds // 3600
            minutes = (td.seconds // 60) % 60
            time = f"{hours:02}:{minutes:02}"
            if completed:
                completed = " ✅"
            else:
                completed = ""
            if isinstance(periods, list):
                period_str = ", ".join(weekdays) if periods else "Без повторений"
            else:
                period_str = periods
            task_text = (f'{completed} {task[1].capitalize()} - '
                         f'{task[2]:%d.%m.%Y} в {time}. Период повторения: {period_str}')
            tasks_list_out.append(task_text)
    task_list_out = ["📌 Список дел:"]
    if len(tasks_list_out) > 0:
        for idx, task in enumerate(tasks_list_out, 1):
            task_text = (f'{idx}) {task}')
            task_list_out.append(task_text)
        full_message = '\n\n'.join(task_list_out)
        return full_message, indexes
    else:
        return False, []

def output_task_today(user_id): #тут будет вывод на сегодня
    current_datetime = datetime.datetime.now().date()
    # если дата уже прошла и не выполнена, то ставим просрочено(надо сделать)
    tasks_list_out = []
    indexes = []
    tasks_list = database.get_all_tasks(user_id)
    for idx, task in enumerate(tasks_list):
        if task[2] == current_datetime:
            indexes.append(idx)
            weekdays = []
            periods = database.output_period_task(task[0])
            for period in periods:
                weekdays.append(database.get_weekday(period))
            completed = task[5]
            td = task[3]
            hours = td.seconds // 3600
            minutes = (td.seconds // 60) % 60
            time = f"{hours:02}:{minutes:02}"
            if completed:
                completed = " ✅"
            if isinstance(periods, list):
                period_str = ", ".join(weekdays) if periods else "Без повторений"
            else:
                period_str = periods
            task_text = (f'{completed} {task[1].capitalize()} - '
                         f'{task[2]:%d.%m.%Y} в {time}. Период повторения: {period_str}')
            tasks_list_out.append(task_text)
    task_list_out = ["📌 Список дел:"]
    if len(tasks_list) > 0:
        for idx, task in enumerate(tasks_list_out, 1):
            task_text = (f'{idx}) {task}')
            task_list_out.append(task_text)
        full_message = '\n\n'.join(task_list_out)
        return full_message, indexes
    else:
        return False, []

@output_task_router.callback_query(F.data == "output")
async def output(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    setting_user = database.output_settings(user_id)
    out = "Не смог вывести список"
    if not tasks_list:
        await call.message.answer("🙁 Список пуст!")
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
    else:
        indexes = []
        if setting_user[3] == 1:
            out= output_task(tasks_list)
        elif setting_user[3] == 2:
            out, indexes = output_task_week(tasks_list)
            if not out:
                await call.message.answer("🙁 Список пуст!")
                bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
                await state.update_data(last_msg_id=bot_msg.message_id)
                return
        elif setting_user[3] == 3:
            out, indexes = output_task_today(user_id)
            if not out:
                await call.message.answer("🙁 Список пуст!")
                bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
                await state.update_data(last_msg_id=bot_msg.message_id)
                return
        await state.update_data(out=out, indexes=indexes)
        await call.message.answer(out, reply_markup=completed_keyboard())

@output_task_router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

@output_task_router.callback_query(F.data == "mark_completed")
async def mark_completed(call: CallbackQuery, state: FSMContext):
    tg_id = str(call.from_user.id)
    data = await state.get_data()
    out_list = data.get("out")
    await call.message.edit_reply_markup(reply_markup=completed_task_keyboard(tg_id, out_list))

@output_task_router.callback_query(F.data.startswith("completed_task_"))
async def completed_task(call: CallbackQuery, state: FSMContext):
    task_num = int(call.data.split("_")[2])
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    data = await state.get_data()
    indexes = data.get("indexes")
    if indexes:
        real_index = indexes[task_num - 1]
    else:
        real_index = task_num - 1
    task_completed = tasks_list[real_index][5]
    if task_completed:
        await call.answer("Эта задача уже отмечена как выполненная!")
    else: #если не выполнена
        database.edit_is_status_task(tasks_list[real_index][0], 1)
        tasks_list = database.get_all_tasks(user_id)
        out_list = ""
        indexes = []
        format_output_id = database.output_settings(user_id)[3]
        if format_output_id == 1:
            out_list = output_task(tasks_list)
            indexes = []
        elif format_output_id == 2:
            out_list, indexes = output_task_week(tasks_list)
        elif format_output_id == 3:
            out_list, indexes = output_task_today(tg_id)
        await state.update_data(out=out_list,indexes=indexes)
        try:
            await call.message.edit_text(text=out_list, reply_markup=completed_task_keyboard(tg_id, task_list=out_list))
        except Exception as e:
            logging.info(f"Ошибка при смене клавиатуры: {e}")


