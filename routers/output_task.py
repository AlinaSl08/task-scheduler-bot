from aiogram.types import CallbackQuery
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import settings_default
from storage import tasks
from aiogram import Router, F

output_task_router = Router()

#вывод по порядку
def output_task(tg_id: int, cap="0"):
    tasks_list = ["📌 Список дел:"]
    for idx, task in enumerate(tasks[tg_id], 1):
        period = task["period"]
        notification = task["notification"]
        if isinstance(period, list):
            period_str = ", ".join(period) if period else "Без повторений"
        else:
            period_str = period
        #тут не работает почему-то
        if notification == 10 or notification == 30:
            notification =  f'Напоминать за {notification} минут.'
        elif notification == 60:
            notification = f'Напоминать за 1 час.'
        elif notification == 120:
            notification = f'Напоминать за 2 часа.'
        if cap == "1":
            task_text = (f'{idx}) {task["name"].capitalize()} - '
                         f'{task["date"]["day"]:02}.{task["date"]["month"]:02}.{task["date"]["year"]} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}. {notification}')
        else:
            task_text = (f'{idx}) {task["name"].capitalize()} - '
                         f'{task["date"]["day"]:02}.{task["date"]["month"]:02}.{task["date"]["year"]} '
                         f'в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}')
        tasks_list.append(task_text)
    full_message = '\n\n'.join(tasks_list)
    return full_message

def output_task_week(tg_id: int): #тут будет вывод на неделю
    return "Функция не доделана!"

def output_task_today(tg_id: int): #тут будет вывод на сегодня
    return "Функция не доделана!"

@output_task_router.callback_query(F.data == "output")
async def output(call: CallbackQuery):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    out = "Не смог вывести список"
    if len(tasks[tg_id]) == 0:
        await call.message.answer("🙁 Список пуст!")
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()
    else:
        if settings_default[tg_id]["format_output"] == 1:
            out = output_task(tg_id)
        elif settings_default[tg_id]["format_output"] == 2:
            out = output_task_week(tg_id)
        elif settings_default[tg_id]["format_output"] == 3:
            out = output_task_today(tg_id)
        await call.message.answer(out)
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()