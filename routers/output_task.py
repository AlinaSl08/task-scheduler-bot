from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.db import save_to_file
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import settings_default, tasks
from aiogram import Router, F
from keyboards.output_task_kb import completed_keyboard, completed_task_keyboard
from commands.command import DATA_FILE_PATH
import datetime


output_task_router = Router()

#вывод по порядку
def output_task(tg_id: str, cap="0", str_task=0):
    tasks_list = ["📌 Список дел:"]
    for idx, task in enumerate(tasks[tg_id], 1):
        period = task["period"]
        notification = task["notification"]
        completed = ""
        if task["completed"]:
            completed = " ✅"
        if isinstance(period, list):
            period_str = ", ".join(period) if period else "Без повторений"
        else:
            period_str = period
        if notification == 10 or notification == 30:
            notification =  f'Напоминать за {notification} минут.'
        elif notification == 60:
            notification = f'Напоминать за 1 час.'
        elif notification == 120:
            notification = f'Напоминать за 2 часа.'
        if cap == "1":
            task_text = (f'{idx}){completed} {task["name"].capitalize()} - '
                         f'{int(task["date"]["day"]):02}.{int(task["date"]["month"]):02}.{int(task["date"]["year"])} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}. {notification}')
        else:
            task_text = (f'{idx}){completed} {task["name"].capitalize()} - '
                         f'{int(task["date"]["day"]):02}.{int(task["date"]["month"]):02}.{int(task["date"]["year"])} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}')
        tasks_list.append(task_text)
    if str_task == 0:
        full_message = '\n\n'.join(tasks_list)
        return full_message
    else:
        return tasks_list[str_task][3:]

def output_task_week(tg_id: str): #тут будет вывод на неделю
    tasks_list = []
    indexes = []
    for idx, task in enumerate(tasks[tg_id]):
        task_day = int(task["date"]["day"])
        task_month = int(task["date"]["month"])
        task_year = int(task["date"]["year"])
        current_date = datetime.date.today()  # сегодняшняя дата
        days_till_monday = datetime.date.weekday(current_date)
        task_date = datetime.date(day=task_day, month=task_month, year=task_year)  # дата задачи
        date_monday = current_date - datetime.timedelta(days=days_till_monday) #дата понедельника с начала недели
        date_sunday = current_date - datetime.timedelta(days=days_till_monday) + datetime.timedelta(days=6)
        if date_sunday >= task_date >= date_monday:
            indexes.append(idx)
            period = task["period"]
            completed = ""
            if task["completed"]:
                completed = " ✅"
            if isinstance(period, list):
                period_str = ", ".join(period) if period else "Без повторений"
            else:
                period_str = period
            task_text = (f'{completed} {task["name"].capitalize()} - '
                         f'{int(task["date"]["day"]):02}.{int(task["date"]["month"]):02}.{int(task["date"]["year"])} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}')
            tasks_list.append(task_text)
    task_list_out = ["📌 Список дел:"]
    if len(tasks_list) > 0:
        for idx, task in enumerate(tasks_list, 1):
            task_text = (f'{idx}) {task}')
            task_list_out.append(task_text)
        full_message = '\n\n'.join(task_list_out)
        return full_message, indexes
    else:
        return False, []

def output_task_today(tg_id: str): #тут будет вывод на сегодня
    current_datetime = datetime.datetime.now()
    current_day = current_datetime.day
    current_month = current_datetime.month
    current_year = current_datetime.year
    tasks_list = []
    indexes = []
    for idx, task in enumerate(tasks[tg_id]):
        task_day = task["date"]["day"]
        task_month = task["date"]["month"]
        task_year =task["date"]["year"]
        if task_day == current_day and current_month == task_month and current_year == task_year:
            indexes.append(idx)
            period = task["period"]
            completed = ""
            if task["completed"]:
                completed = " ✅"
            if isinstance(period, list):
                period_str = ", ".join(period) if period else "Без повторений"
            else:
                period_str = period
            task_text = (f'{completed} {task["name"].capitalize()} - '
                         f'{int(task["date"]["day"]):02}.{int(task["date"]["month"]):02}.{int(task["date"]["year"])} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}')
            tasks_list.append(task_text)
    task_list_out = ["📌 Список дел:"]
    if len(tasks_list) > 0:
        for idx, task in enumerate(tasks_list, 1):
            task_text = (f'{idx}) {task}')
            task_list_out.append(task_text)
        full_message = '\n\n'.join(task_list_out)
        return full_message, indexes
    else:
        return False, []



@output_task_router.callback_query(F.data == "output")
async def output(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    tg_id = str(call.from_user.id)
    out = "Не смог вывести список"
    if len(tasks[tg_id]) == 0:
        await call.message.answer("🙁 Список пуст!")
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
        await call.answer()
    else:
        indexes = []
        if settings_default[tg_id]["format_output"] == 1:
            out= output_task(tg_id)
        elif settings_default[tg_id]["format_output"] == 2:
            out, indexes = output_task_week(tg_id)
            if not out:
                await call.message.answer("🙁 Список пуст!")
                bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
                await state.update_data(last_msg_id=bot_msg.message_id)
                await call.answer()
                return
        elif settings_default[tg_id]["format_output"] == 3:
            out, indexes = output_task_today(tg_id)
            if not out:
                await call.message.answer("🙁 Список пуст!")
                bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
                await state.update_data(last_msg_id=bot_msg.message_id)
                await call.answer()
                return
        await state.update_data(out=out, indexes=indexes)
        await call.message.answer(out, reply_markup=completed_keyboard())
        await call.answer()

@output_task_router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await call.answer()

@output_task_router.callback_query(F.data == "mark_completed")
async def mark_completed(call: CallbackQuery, state: FSMContext):
    tg_id = str(call.from_user.id)
    data = await state.get_data()
    out_list = data.get("out")
    await call.message.edit_reply_markup(reply_markup=completed_task_keyboard(tg_id, task_list=out_list))

@output_task_router.callback_query(F.data.startswith("completed_task_"))
async def completed_task(call: CallbackQuery, state: FSMContext):
    task_num = int(call.data.split("_")[2])
    tg_id = str(call.from_user.id)
    data = await state.get_data()
    indexes = data.get("indexes")
    if indexes:
        real_index = indexes[task_num - 1]
    else:
        real_index = task_num - 1
    task_completed = tasks[tg_id][real_index]["completed"]
    if not task_completed:
        tasks[tg_id][real_index]["completed"] = True
        save_to_file(DATA_FILE_PATH, tasks)
        out_list = ""
        indexes = []
        format_output = settings_default[tg_id]["format_output"]
        if format_output == 1:
            out_list = output_task(tg_id)
            indexes = []
        elif format_output == 2:
            out_list, indexes = output_task_week(tg_id)
        elif format_output == 3:
            out_list, indexes = output_task_today(tg_id)
        await state.update_data(out=out_list,indexes=indexes)
        try:
            await call.message.edit_reply_markup(reply_markup=completed_task_keyboard(tg_id, task_list=out_list))
        except Exception as e:
            print("Ошибка при смене клавиатуры:", e)
    else:
        await call.answer("Эта задача уже отмечена как выполненная!")

