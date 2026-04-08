from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram import Bot
from states.add_task_state import AddTask
from datetime import datetime
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.add_task_kb import get_date_keyboard, get_time_hour_keyboard, get_time_minute_keyboard, get_period_keyboard, get_notification_keyboard
from keyboards.main_kb import main_menu_keyboard
from states.edit_task_state import EditTask
from states.menu_state import Menu
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.database import database
import logging
from utils.scheduler import schedule_all_tasks, add_overdue_checker, schedule_single_task

add_task_router = Router()

days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

@add_task_router.callback_query(F.data == "add")
async def add_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    await state.update_data()
    bot_msg = await call.message.answer("Напишите название задачи:")
    await call.answer()
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.name)

# часы 1 часть
@add_task_router.callback_query(F.data.startswith("next_hour"))
async def next_hour(call: CallbackQuery):
    mode_time = call.data.split("_")[2]
    if mode_time == "add":
        await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(2, mode_key=1))
    else:
        await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(2, mode_key=2))

# часы 2 часть
@add_task_router.callback_query(F.data.startswith("prev_hour"))
async def prev_hour(call: CallbackQuery):
    mode_time = call.data.split("_")[2]
    if mode_time == "add":
        await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(1, mode_key=1))
    else:
        await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(1, mode_key=2))

# часы
@add_task_router.callback_query(F.data.startswith("hour_"))
async def hour_task(call: CallbackQuery, state: FSMContext):
    hour = call.data.split("_")[2]
    mode_time = call.data.split("_")[1]
    data = await state.get_data()
    if mode_time == "add":
        today_date = data.get("real_date_str")
        selected_date = data.get("date")
    else:
        today_date = data.get("current_datetime")
        number_task = data.get("number_task")
        tg_id = str(call.from_user.id)
        user_id = database.get_user_id(tg_id)
        task_date = database.get_all_tasks(user_id)[number_task - 1][2]
        selected_date = task_date
    now = datetime.now()
    today_time = now.strftime("%H:%M:%S").split(":") #время сейчас
    if len(hour) == 1:
        hour = "0" + hour
    same_hour = 0
    if today_date == selected_date: #если дата выбрана такая же, как сейчас, делаем проверку
        if today_time[0] == hour:
            same_hour = 1 #если час такой же как сейчас
        elif today_time[0] > hour:
            await call.answer("Час уже прошел, попробуйте снова")
            return
    await state.update_data(same_hour=same_hour)
    if mode_time == "add":
        await call.message.edit_reply_markup(reply_markup=get_time_minute_keyboard(hour, mode_key=1))
    else:
        bot_msg = await call.message.edit_reply_markup(reply_markup=get_time_minute_keyboard(hour, mode_key=2))
        await state.update_data(bot_msg_id=bot_msg.message_id)

# переход от времени к периоду, проверка минут
@add_task_router.callback_query(F.data.startswith("time_"))
async def time_task(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    time = call.data.split("_")[2]
    mode_time = call.data.split("_")[1]
    minute = time.split(":")[1]
    hour = time.split(":")[0]
    data = await state.get_data()
    same_hour = data.get("same_hour")
    await safe_delete(call.message)
    now = datetime.now()
    today_time = now.strftime("%H:%M:%S").split(":")
    if same_hour == 1 and int(today_time[1]) >= int(minute):
        await call.answer("Время уже прошло, попробуйте снова")
        if mode_time == "add":
            await call.message.answer("Выберите время выполнения задачи:",
                                      reply_markup=get_time_minute_keyboard(hour, mode_key=1))
        else:
            await call.message.answer("Выберите время выполнения задачи:",
                                      reply_markup=get_time_minute_keyboard(hour, mode_key=2))
        return
    if mode_time == "add":
        selected = [0, 0, 0, 0, 0, 0, 0]
        bot_msg = await call.message.answer("По каким дням недели будет повторяться задача?:",
                                       reply_markup=get_period_keyboard())
        await state.update_data(time=time, last_msg_id=bot_msg.message_id, selected_days=selected)
        await state.set_state(AddTask.period)
    else:
        tg_id = str(call.from_user.id)
        user_id = database.get_user_id(tg_id)
        number_task = data.get("number_task")
        task_id = database.get_all_tasks(user_id)[number_task - 1][0]
        database.edit_time_task(task_id,f'{hour}:{minute}:00')
        scheduler.remove_all_jobs()
        schedule_all_tasks(scheduler, bot)
        add_overdue_checker(scheduler)
        tasks_message_id_out = data.get("tasks_list_id")
        await delete_last_message(tasks_message_id_out, call.message)
        await call.message.answer("✅ Время задачи изменено!")
        await state.clear()
        await state.set_state(Menu.menu)
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
    await call.answer()

# без периода повторения
@add_task_router.callback_query(F.data == "no_period")
async def period_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Задача повторяться не будет!")
    bot_msg = await call.message.answer("За сколько напомнить о задаче?:", reply_markup=get_notification_keyboard())
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(selected_days=[], last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.notification)
    await call.answer()

# период повторения
@add_task_router.callback_query(F.data.startswith("period_"))
async def period_task(call: CallbackQuery, state: FSMContext):
    try:
        period = int(call.data.split("_")[2])
        period_mode = call.data.split("_")[1]
        data = await state.get_data()
        selected_days = data.get("selected_days")
        if selected_days[period] == 1:
            await call.answer("Этот день уже выбран 😉")
            return
        selected_days[period] = 1
        if period_mode == "add":
            await call.message.edit_reply_markup(
                reply_markup=get_period_keyboard(selected=selected_days, no_period=1, mode_key=1))
        else:
            await call.message.edit_reply_markup(
                reply_markup=get_period_keyboard(selected=selected_days, no_period=1, mode_key=2))
        await state.update_data(selected_days=selected_days)
    except Exception as e:
        await call.answer("Произошла ошибка, попробуйте снова")
        logging.info(f"Название ошибки: {e}")
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
        await call.answer()

@add_task_router.callback_query(F.data == "continue_get_period")
async def continue_get_period(call: CallbackQuery, state: FSMContext):
    bot_msg = await call.message.answer("За сколько напомнить о задаче?:",
                                        reply_markup=get_notification_keyboard())
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.notification)
    await call.answer()

#конвертер периода в дни недели
def convert_selected_days_to_str(selected_days):
    result = []
    for i in range(len(selected_days)):
        if selected_days[i] == 1:
            result.append(days[i])
    return result

#сохраняем задачу
@add_task_router.callback_query(F.data.startswith("notification_"))
async def notification_task(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler = None):
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    task_id = 0
    try:
        bot = call.bot
        notification = int(call.data.split("_")[2]) #если 0, то нет напоминаний
        notification_id = database.get_notification_id(notification)
        notification_mode = call.data.split("_")[1]
        data = await state.get_data()
        if notification_mode == "add":
            last_msg_id = data.get("last_msg_id")
            await delete_last_message(last_msg_id, call.message)
            name = data["name"]
            date = data["date"]
            time_list = list(map(int, data["time"].split(":")))
            time = f'{time_list[0]}:{time_list[1]:00}'
            task_id = database.save_task(user_id, name, date, time, notification_id)  # добавляем задачу
            period_days = convert_selected_days_to_str(data["selected_days"])
            if period_days: #если список пуст, то период не добавляем
                for day in period_days:
                    period_day_id = database.get_weekday_id(day)
                    database.save_period_task(task_id, period_day_id) # добавляем период
            task = database.get_task_by_id(task_id)[0]
            print(task)
            schedule_single_task(scheduler, bot, user_id, tg_id, task)
            bot_msg = await call.message.answer("✅ Задача успешно добавлена!")
            await state.update_data(last_msg_id=bot_msg.message_id)
        else:
            number_task = data.get("number_task")
            task_id = database.get_all_tasks(user_id)[number_task - 1][0]
            database.edit_notification_task(task_id, notification_id)
            schedule_all_tasks(scheduler, bot)
            bot_msg_id = data.get("bot_msg_id")
            tasks_message_id_out = data.get("tasks_list_id")
            await delete_last_message(tasks_message_id_out, call.message)
            await delete_last_message(bot_msg_id, call.message)
            await call.message.answer("✅ Напоминание задачи изменено!")
    except Exception as e:
        #удаление задачи если ошибка и если она есть
        if task_id:
            database.delete_task(user_id, task_id)
        logging.info(f"Ошибка при добавлении задачи: {e}")
        await call.answer("Ошибка при добавлении задачи.")
    finally:
        await state.clear()
        await state.set_state(Menu.menu)
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)

#-ФУНКЦИИ КЛАВИАТУРЫ ДАТЫ-
#если нажмет пустую стрелочку, на месяц и год, на день недели (заглушка)
@add_task_router.callback_query(F.data == "cap")
async def cap(call: CallbackQuery):
    await call.answer("Ошибка, попробуйте снова")

#если нажмет на стрелочку вперед
@add_task_router.callback_query(F.data == "next_month")
async def next_month(call: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        current_month = data.get("current_month")
        current_year = data.get("current_year")
        if current_month == 12:
            edit_month = 1
            current_year += 1
        else:
            edit_month = current_month + 1
        await state.update_data(current_month=edit_month, current_year=current_year)
        await call.message.edit_reply_markup(reply_markup=get_date_keyboard(
            current_month=edit_month, current_year=current_year, cap="<"))
    except Exception as e:
        logging.info(f"Ошибка. Следующий месяц не существует. Название ошибки: {e}" )
        await call.answer("Ошибка")

#если нажмет активную стрелку назад
@add_task_router.callback_query(F.data == "last_month")
async def last_month(call: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        current_month = data.get("current_month")
        current_year = data.get("current_year")
        real_current_month = data.get("real_current_month")
        real_current_year = data.get("real_current_year")
        if current_month == 1:
            edit_month = 12
            current_year -= 1
        else:
            edit_month = current_month - 1
        await state.update_data(current_month=edit_month, current_year=current_year)
        if edit_month == real_current_month and current_year == real_current_year:
            await call.message.edit_reply_markup(
                                  reply_markup=get_date_keyboard(
                                      current_month=edit_month, current_year=current_year, cap=" "))
        else:
            await call.message.edit_reply_markup(
                                      reply_markup=get_date_keyboard(
                                          current_month=edit_month, current_year=current_year, cap="<"))
    except Exception as e:
        logging.info(f"Ошибка. Предыдущий месяц не существует. Название ошибки: {e}")
        await call.answer("Ошибка")

#если нажимает на дату
@add_task_router.callback_query(F.data.startswith("date_"))
async def choose_date(call: CallbackQuery, state: FSMContext, scheduler: AsyncIOScheduler, bot: Bot):
    date_day = int(call.data.split("_")[2])
    mode = call.data.split("_")[1]
    data = await state.get_data()
    date_month = data.get("current_month")
    date_year = data.get("current_year")
    real_date_month = data.get("real_current_month")
    real_date_year = data.get("real_current_year")
    real_date_day = data.get("real_current_day")
    #если дата уже прошла
    if real_date_day > date_day and date_month == real_date_month and real_date_year == date_year:
        await call.answer("Дата уже прошла, попробуйте снова")
        return
    real_date_str = f"{real_date_year}-{real_date_month}-{real_date_day}"
    date_str = f"{date_year}-{date_month}-{date_day}"
    if mode == "edit":
        number_task = data.get("number_task")
        now = datetime.now()
        tg_id = str(call.from_user.id)
        user_id = database.get_user_id(tg_id)
        tasks_list = database.get_all_tasks(user_id)
        task_time = tasks_list[number_task - 1][3]
        if hasattr(task_time, 'total_seconds'): #проверяет, есть ли у объекта метод или свойство с таким названием.
            total_seconds = int(task_time.total_seconds())
        else:
            total_seconds = int(task_time) #извлекаем часы и минуты из timedelta
        task_hour = total_seconds // 3600  # часы в задаче
        task_minute = (total_seconds % 3600) // 60  # минуты в задаче
        now_hour = now.hour # часы сейчас
        now_minute = now.minute # минуты сейчас
        if real_date_str == date_str:
            if task_hour <= now_hour :# если час такой же как и сейчас или больше
                if task_minute < now_minute:
                    await call.answer("Невозможно выбрать эту дату! Измените сначала время задачи")
                    return
                elif task_minute == now_minute:
                    await call.answer("Эта дата уже выбрана!")
                    return
                else:
                    database.edit_date_task(tasks_list[number_task - 1][0], date_str)
                    scheduler.remove_all_jobs()
                    schedule_all_tasks(scheduler, bot)
                    add_overdue_checker(scheduler)
                    tasks_message_id_out = data.get("tasks_list_id")
                    await delete_last_message(tasks_message_id_out, call.message)
                    await safe_delete(call.message)
                    await call.message.answer("✅ Дата выполнения задачи успешно изменена!")
                    await state.set_state(EditTask.date)
                    await state.clear()
                    await state.set_state(Menu.menu)
                    bot_msg = await call.message.answer("Выберите действие:",
                                                        reply_markup=main_menu_keyboard())
                    await state.update_data(last_msg_id=bot_msg.message_id)
                    await call.answer()
                    return
            elif now_hour > task_hour:
                await call.answer("Невозможно выбрать эту дату! Измените сначала время задачи")
                return
        else:
            database.edit_date_task(tasks_list[number_task - 1][0], date_str)
            scheduler.remove_all_jobs()
            schedule_all_tasks(scheduler, bot)
            add_overdue_checker(scheduler)
            tasks_message_id_out = data.get("tasks_list_id")
            await delete_last_message(tasks_message_id_out, call.message)
            await safe_delete(call.message)
            await call.message.answer("✅ Дата выполнения задачи успешно изменена!")
            await state.clear()
            await state.set_state(Menu.menu)
            bot_msg = await call.message.answer("Выберите действие:",
                                                reply_markup=main_menu_keyboard())
            await state.update_data(last_msg_id=bot_msg.message_id)
            await call.answer()
            return
    else:
        await state.update_data(date=date_str, real_date_str=real_date_str)
        await safe_delete(call.message)
        await state.set_state(AddTask.time)
        await call.message.answer("Выберите время выполнения задачи:",
                                  reply_markup=get_time_hour_keyboard())
        await call.answer()

# добавляем имя
@add_task_router.message(AddTask.name)
async def get_name(message: Message, state: FSMContext):
    name = message.text
    # получаем текущую дату
    current_datetime = datetime.now()
    current_day = current_datetime.day
    current_month = current_datetime.month
    current_year = current_datetime.year
    #текущее число (сегодня) для проверки на прошедшие даты
    real_current_day = current_datetime.day
    real_current_month = current_datetime.month
    real_current_year = current_datetime.year
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(name=name, current_day=current_day,
                            current_month=current_month, current_year=current_year,
                            real_current_month=real_current_month, real_current_year=real_current_year,
                            real_current_day=real_current_day)
    bot_msg = await message.answer("Выберите дату выполнения задачи:",
                                   reply_markup=get_date_keyboard(current_month=current_month,
                                                                  current_year=current_year))
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.date)

# добавляем дату
@add_task_router.message(AddTask.date)
async def ignore_get_date(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите дату с помощью кнопок ниже 👇", reply_markup=get_date_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем время
@add_task_router.message(AddTask.time)
async def ignore_time_text(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_time_hour_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем период
@add_task_router.message(AddTask.period)
async def ignore_period_text(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_period_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем уведомление
@add_task_router.message(AddTask.notification)
async def get_notification(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_notification_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)