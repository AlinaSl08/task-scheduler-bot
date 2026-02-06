from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from states.add_task import AddTask
from datetime import datetime
from utils.delete_last_message import safe_delete, delete_last_message
from database.db import save_to_file
from keyboards.add_task_kb import get_date_keyboard, get_time_hour_keyboard, get_time_minute_keyboard, get_period_keyboard, get_notification_keyboard
from keyboards.main_kb import main_menu_keyboard
from storage.tasks import tasks
from commands.command import path_to_data

add_task_router = Router()

days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

@add_task_router.callback_query(F.data == "add") #обработчик кнопки
async def add_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    await state.update_data()  # создаем хранилище, хранит шаг и файл
    bot_msg = await call.message.answer("Напишите название задачи:") #у call обратиться к сообщению и записали туда текст
    await call.answer() #а тут отправляем измененное сообщение обратно
    await state.update_data(last_msg_id=bot_msg.message_id) #сохраняем айди сообщения
    await state.set_state(AddTask.name) #задает начало цепочки(откуда стартовать)

# часы 1 часть
@add_task_router.callback_query(F.data == "next_hour")
async def next_hour(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(2))

# часы 2 часть
@add_task_router.callback_query(F.data == "prev_hour")
async def prev_hour(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(1))

# минуты
@add_task_router.callback_query(F.data.startswith("hour_"))
async def hour_task(call: CallbackQuery, state: FSMContext):
    hour = call.data.split("_")[1]
    data = await state.get_data()
    today_date = data.get("real_date_str")
    selected_date = data.get("date")
    now = datetime.now()
    today_time = now.strftime("%H:%M:%S").split(":")
    if len(hour) == 1:
        hour = "0" + hour
    same_hour = 0
    if today_date == selected_date:
        if today_time[0] == hour:
            same_hour = 1 #если час такой же как сейчас
        elif today_time[0] > hour:
            await call.answer("Час уже прошел, попробуйте снова")
            return
    await state.update_data(same_hour=same_hour)
    await call.message.edit_reply_markup(reply_markup=get_time_minute_keyboard(hour))

# переход от времени к периоду
@add_task_router.callback_query(F.data.startswith("time_"))
async def time_task(call: CallbackQuery, state: FSMContext):
    time = call.data.split("_")[1]
    minute = time.split(":")[1]
    hour = time.split(":")[0]
    data = await state.get_data()
    same_hour = data.get("same_hour")
    await safe_delete(call.message)
    now = datetime.now()
    today_time = now.strftime("%H:%M:%S").split(":")
    if same_hour == 1 and int(today_time[1]) >= int(minute):
        await call.answer("Время уже прошло, попробуйте снова")
        await call.message.answer("Выберите время выполнения задачи:", reply_markup=get_time_minute_keyboard(hour))
        await call.answer()
        return
    selected = [0, 0, 0, 0, 0, 0, 0]
    bot_msg = await call.message.answer("По каким дням недели будет повторяться задача?:",
                                   reply_markup=get_period_keyboard())
    await state.update_data(time=time, last_msg_id=bot_msg.message_id, selected_days=selected)
    await state.set_state(AddTask.period)
    await call.answer()

# без периода повторения
@add_task_router.callback_query(F.data == "no_period")
async def period_no(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Задача повторяться не будет!")
    period = 'Без повторений'
    bot_msg = await call.message.answer("За сколько напомнить о задаче?:", reply_markup=get_notification_keyboard())
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(period=period, last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.notification)
    await call.answer()

# период повторения
@add_task_router.callback_query(F.data.startswith("period_"))
async def period_task(call: CallbackQuery, state: FSMContext):
    try:
        period = int(call.data.split("_")[1])
        data = await state.get_data()
        selected_days = data.get("selected_days")

        if selected_days[period] == 1:
            await call.answer("Этот день уже выбран 😉")
            return

        selected_days[period] = 1
        await call.message.edit_reply_markup(reply_markup=get_period_keyboard(selected=selected_days, no_period=1))
        await state.update_data(selected_days=selected_days)
    except Exception:
        await call.answer("Произошла ошибка, попробуйте снова")
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await call.answer()


@add_task_router.callback_query(F.data.startswith("continue_get_period"))
async def continue_get_period(call: CallbackQuery, state: FSMContext):
    bot_msg = await call.message.answer("За сколько напомнить о задаче?:", reply_markup=get_notification_keyboard())
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

#напоминания до задачи есть
@add_task_router.callback_query(F.data.startswith("notification_"))
async def notification_task(call: CallbackQuery, state: FSMContext):
    notification = int(call.data.split("_")[1])

    bot_msg = await call.message.answer("✅ Задача успешно добавлена!")
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(notification=notification, last_msg_id=bot_msg.message_id)
    data = await state.get_data()
    name = data["name"]
    date = list(map(int, data["date"].split(".")))
    date = {"day": date[0], "month": date[1], "year": date[2]}
    time = list(map(int, data["time"].split(":")))
    time = {"hour": time[0], "minute": time[1]}
    period = convert_selected_days_to_str(data["selected_days"])
    notification = data["notification"]
    # добавляем задачу в список
    tg_id = call.from_user.id
    tasks[tg_id].append({"name": name, "date": date, "time": time, "period": period, "notification": notification})
    print(tasks)
    save_to_file(path_to_data, tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

#не напоминать до задачи
@add_task_router.callback_query(F.data == "no_notification")
async def notification_task(call: CallbackQuery, state: FSMContext):
    notification = "Без напоминаний"
    bot_msg = await call.message.answer("✅ Задача успешно добавлена!")
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(notification=notification, last_msg_id=bot_msg.message_id)
    data = await state.get_data()
    name = data["name"]
    date = list(map(int, data["date"].split(".")))
    date = {"day": date[0], "month": date[1], "year": date[2]}
    time = list(map(int, data["time"].split(":")))
    time = {"hour": time[0], "minute": time[1]}
    period = data.get("period", "Без повторений")
    notification = data["notification"]
    # добавляем задачу в список
    tg_id = call.from_user.id
    tasks[tg_id].append({"name": name, "date": date, "time": time, "period": period, "notification": notification})
    print(tasks)
    save_to_file(path_to_data, tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

#-ФУНКЦИИ КЛАВИАТУРЫ ДАТЫ-
#если нажмет пустую стрелочку и если нажмет на месяц и год и если нажимает на день недели
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
        await call.message.edit_reply_markup(reply_markup=get_date_keyboard(current_month=edit_month, current_year=current_year, cap="<"))
    except:
        print("Ошибка. Следующий месяц не существует")
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
                                  reply_markup=get_date_keyboard(current_month=edit_month, current_year=current_year, cap=" "))
        else:
            await call.message.edit_reply_markup(
                                      reply_markup=get_date_keyboard(current_month=edit_month, current_year=current_year, cap="<"))
    except:
        print("Ошибка. Предыдущий месяц не существует")
        await call.answer("Ошибка")

#если нажимает на дату
@add_task_router.callback_query(F.data.startswith("date_"))
async def choose_date(call: CallbackQuery, state: FSMContext):
    date_day = int(call.data.split("_")[1])
    data = await state.get_data()
    date_month = data.get("current_month")
    date_year = data.get("current_year")

    real_date_month = data.get("real_current_month")
    real_date_year = data.get("real_current_year")
    real_date_day = data.get("real_current_day")
    print(data)
    print(real_date_day)
    print(date_day)
    #если дата уже прошла
    if real_date_day > date_day and date_month == real_date_month and real_date_year == date_year:
        await call.answer("Дата уже прошла, попробуйте снова")
        return
    real_date_str = f"{real_date_day}.{real_date_month}.{real_date_year}"
    date_str = f"{date_day}.{date_month}.{date_year}"
    await state.update_data(date=date_str, real_date_str=real_date_str)
    await safe_delete(call.message)
    await state.set_state(AddTask.time)
    await call.message.answer("Выберите время выполнения задачи:", reply_markup=get_time_hour_keyboard())
    await call.answer()

# добавляем имя
@add_task_router.message(AddTask.name)
async def get_name(message: Message, state: FSMContext): #название задачи
    name = message.text #то что получили кладем в переменную
    # получаем текущую дату
    current_datetime = datetime.now()
    current_day = current_datetime.day
    current_month = current_datetime.month
    current_year = current_datetime.year

    real_current_day = current_datetime.day
    real_current_month = current_datetime.month
    real_current_year = current_datetime.year


    data = await state.get_data()
    last_msg_id = data.get("last_msg_id") #получаем айди предыдущего сообщения
    await delete_last_message(last_msg_id, message)
    # обновить значение(как ключ:значение) и сохранить
    await state.update_data(name=name, current_day=current_day,
                            current_month=current_month, current_year=current_year, real_current_month=real_current_month,
                            real_current_year=real_current_year, real_current_day=real_current_day)
    bot_msg = await message.answer("Выберите дату выполнения задачи:",
                                   reply_markup=get_date_keyboard(current_month=current_month,
                                                                  current_year=current_year))
    await state.update_data( last_msg_id=bot_msg.message_id)
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