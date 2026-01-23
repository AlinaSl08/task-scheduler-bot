import asyncio
import logging

import aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand

import calendar
from datetime import datetime
from dotenv import load_dotenv
import os
import json


#сделать напоминания по времени
#доделать кнопку изменения
#подключить бд
#сделать статистику по выполненным задачам
#сделать кнопки выполнения задач
#сделать архитектуру

#если пишу часы текстом, то сообщение дает уведу но не удаляет предыдущ сообщение, если пользователь на середине нажжал на старт то может продолжить создание задачи и потом выдает ошибку
#если пользователь остановился на моменте создания задачи и потом вернулся заново и попытался задачу добавить(в новой сессии запуска бота), то вылетает ошибка потому что не находит предыдущие внесенные ключи

#доделать баг с временем прошлым
#сделать вывод задач сегодня\на неделю
#доделать изменение задач, я не понимаю как подключить старые кнопки как при добавлении

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage()) #хранит состояние пользователя(на каком шаге находится)

logging.basicConfig(level=logging.INFO) #уровень логирования

main_router = Router()
dp.include_router(main_router) #добавляет роутер в поле зрения(в диспетчер)

# Запись и чтение в JSON
def save_to_file(file_name, dictionary):
    try:
        with open(file_name, 'w', encoding='utf8') as f:
            json_data = json.dumps(dictionary)
            f.write(json_data)
    except Exception as e:
        print("Ошибка, при сохранении файла")

def read_from_file(file_name, dictionary):
    try:
        with open(file_name, 'r', encoding='utf8') as f:
            json_input = f.read()
            info = json.loads(json_input)
            print(dictionary)
            for key, item in info.items():
                dictionary[int(key)] = item
            print(dictionary)
    except Exception as e:
        print("Произошла ошибка, при считывании файла:", e)

tasks = {}
read_from_file('data.json', tasks)


settings_default = {}
read_from_file('settings.json', settings_default)

days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
settings_transcript = {
    "timezone":{
        0: "МСК", -1: "МСК-1", 2: "МСК+1", 3: "МСК+2", 4: "МСК+3", 5: "МСК+4",
        6: "МСК+5", 7: "МСК+6", 8: "МСК+7", 9: "МСК+8", 10: "МСК+9"},
    "sort":{
        1: "По порядку",
        2: "По названию",
        3: "По дате",
        4: "По времени"},
    "format_output": {
        1: "Все задачи",
        2: "Задачи на неделю",
        3: "Задачи сегодня"}
    }

# функция удаления предыдущего сообщения
async def delete_last_message(last_msg_id: int, message: Message):
    if last_msg_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, #айди текущего смс
                message_id=last_msg_id #айди смс которое хотим удалить
            )
        except aiogram.exceptions.TelegramBadRequest as tbr:
            print("При удалении несуществующего сообщения произошла ошибка!")

#удаление предыдущих сообщений с проверкой
async def safe_delete(message: Message):
    try:
        await message.delete()
    except aiogram.exceptions.TelegramBadRequest:
        pass

#--МЕНЮ--
def main_menu_keyboard():
    kb = InlineKeyboardBuilder() #создаем клавиатуру
    kb.button(text="✔️ Добавить", callback_data="add") #вызов команды, callback_data - данные о вызове
    kb.button(text="🗑️ Удалить", callback_data="delete")
    kb.button(text="💻 Вывести список", callback_data="output")
    kb.button(text="🖊️ Изменить задачу", callback_data="change")
    kb.button(text="❌ Очистить список задач", callback_data="clear")
    kb.button(text="⚙️ Настройки", callback_data="settings")
    kb.adjust(2) #сколько кнопок на строке
    return kb.as_markup() #превращаем в объект клавиатуры


#--СПИСОК КОМАНД--
class Auth(StatesGroup):
    timezone = State()

@main_router.message(Command("start"))
async def start(message: Message, state: FSMContext): #обозначаем что мы дадим в функцию(какой тип данных)
    if message.chat.id not in tasks:
        tasks[message.chat.id] = [] #тут сохраняется строка
        tg_id = message.from_user.id #тут сохраняется число
        settings_default[tg_id] = {'format_output': 1, 'sort': 1, 'timezone': 0}
        save_to_file('data.json', tasks)
        save_to_file('settings.json', settings_default)
        bot_msg = await message.answer("👋 Добро пожаловать!\n\nЭтот бот поможет вам планировать задачи и напоминания.\nДля начала выберите ваш часовой пояс:", reply_markup=timezone_keyboard())
        await state.update_data(start_msg=bot_msg.message_id)
        await state.set_state(Auth.timezone)
    else:
        await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

@main_router.message(Auth.timezone)
async def ignore_timezone(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите часовой пояс с помощью кнопок ниже 👇", reply_markup=timezone_keyboard()
    )
    data = await state.get_data()
    start_msg = data.get("start_msg")
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(start_msg, message)
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

#клавиатура часвого пояса в начале
def timezone_keyboard():
    kb = InlineKeyboardBuilder()
    for number in ["-1", "0", "+1", "+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9"]:
        if number == "0":
            kb.button(text=f"🌍 МСК", callback_data=f"default_utc_{number}")
        else:
            kb.button(text=f"🌍 МСК{number}", callback_data=f"default_utc_{number}")
    kb.adjust(3, 3, 3, 2)
    return kb.as_markup()

#сохранение часового пояса по умолчанию
@main_router.callback_query(F.data.startswith ("default_utc_"))
async def utc_selection_default(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number = int(call.data.split("_")[2])
    tg_id = call.from_user.id
    settings_default[tg_id]['timezone'] = number
    print(settings_default)
    save_to_file('settings.json', settings_default)
    await call.answer("Настройки применены!")
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())


@main_router.message(Command("help"))
async def help(message: Message):
    await message.answer("Список доступных команд бота: \n/start\n/menu\n/help\n/settings")

@main_router.message(Command("menu"))
async def menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

def settings_output(tg_id):
    tz = settings_default[tg_id]['timezone']
    srt = settings_default[tg_id]['sort']
    form_out = settings_default[tg_id]['format_output']
    return f'⚙️ Ваши настройки:\n\n🌍 Часовой пояс: {settings_transcript["timezone"][tz]}\n📌 Сортировка: {settings_transcript["sort"][srt]}\n📄 Формат вывода задач: {settings_transcript["format_output"][form_out]}\n\nЧтобы изменить параметры, откройте раздел «Настройки» в главном меню.'


#вывод настроек пользователя
@main_router.message(Command("settings"))
async def settings(message: Message):
    tg_id = message.from_user.id
    await message.answer(settings_output(tg_id))
    await message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())

# создание подсказать к командам при вводе /
async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Показать меню"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="settings", description="Активные настройки")
    ]
    await bot.set_my_commands(commands) # отправляем телеграм список команд бота


#--ДОБАВЛЕНИЕ--
class AddTask(StatesGroup):
    name = State()
    date = State()
    time = State()
    period = State()
    notification = State()

@main_router.callback_query(F.data == "add") #обработчик кнопки
async def add_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    await state.update_data()  # создаем хранилище, хранит шаг и файл
    bot_msg = await call.message.answer("Напишите название задачи:") #у call обратиться к сообщению и записали туда текст
    await call.answer() #а тут отправляем измененное сообщение обратно
    await state.update_data(last_msg_id=bot_msg.message_id) #сохраняем айди сообщения
    await state.set_state(AddTask.name) #задает начало цепочки(откуда стартовать)

#-ФУНКЦИИ КЛАВИАТУРЫ-

# часы 1 часть
@main_router.callback_query(F.data == "next_hour")
async def next_hour(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(2))

# часы 2 часть
@main_router.callback_query(F.data == "prev_hour")
async def prev_hour(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=get_time_hour_keyboard(1))

# минуты
@main_router.callback_query(F.data.startswith("hour_"))
async def hour_task(call: CallbackQuery, state: FSMContext):
    hour = call.data.split("_")[1]
    if len(hour) == 1:
        hour = "0" + hour
    await call.message.edit_reply_markup(reply_markup=get_time_minute_keyboard(hour))

# переход от времени к периоду
@main_router.callback_query(F.data.startswith("time_"))
async def time_task(call: CallbackQuery, state: FSMContext):
    time = call.data.split("_")[1]
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await safe_delete(call.message)
    #await delete_last_message(last_msg_id, call.message)
    selected = [0, 0, 0, 0, 0, 0, 0]
    bot_msg = await call.message.answer("По каким дням недели будет повторяться задача?:",
                                   reply_markup=get_period_keyboard())

    await state.update_data(time=time, last_msg_id=bot_msg.message_id, selected_days=selected)
    await state.set_state(AddTask.period)
    await call.answer()

# без периода повторения
@main_router.callback_query(F.data == "no_period")
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
@main_router.callback_query(F.data.startswith("period_"))
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


@main_router.callback_query(F.data.startswith("continue_get_period"))
async def continue_get_period(call: CallbackQuery, state: FSMContext):
    bot_msg = await call.message.answer("За сколько напомнить о задаче?:", reply_markup=get_notification_keyboard())
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, call.message)
    await state.update_data(last_msg_id=bot_msg.message_id)
    await state.set_state(AddTask.notification)
    await call.answer()

#напоминания до задачи есть
@main_router.callback_query(F.data.startswith("notification_"))
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
    save_to_file('data.json', tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

#не напоминать до задачи
@main_router.callback_query(F.data == "no_notification")
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
    save_to_file('data.json', tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

#-ФУНКЦИИ КЛАВИАТУРЫ ДАТЫ-
#если нажмет пустую стрелочку и если нажмет на месяц и год и если нажимает на день недели
@main_router.callback_query(F.data == "cap")
async def cap(call: CallbackQuery):
    await call.answer("Ошибка, попробуйте снова")


#если нажмет на стрелочку вперед
@main_router.callback_query(F.data == "next_month")
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
@main_router.callback_query(F.data == "last_month")
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
@main_router.callback_query(F.data.startswith("date_"))
async def choose_date(call: CallbackQuery, state: FSMContext):
    date_day = int(call.data.split("_")[1])
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
    date_str = f"{date_day}.{date_month}.{date_year}"
    await state.update_data(date=date_str)
    await safe_delete(call.message)
    await state.set_state(AddTask.time)
    await call.message.answer("Напишите время выполнения задачи в формате ЧЧ:ММ:", reply_markup=get_time_hour_keyboard())
    await call.answer()


#-КЛАВИАТУРЫ-

# клавиатура даты
def get_date_keyboard(current_month=1, current_year=2026, cap=" "):
    #делаем клавиатуру
    kb = InlineKeyboardBuilder()
    calendar_for_keyboard = calendar.Calendar().monthdayscalendar(current_year, current_month)
    new_calendar = []
    for days in calendar_for_keyboard:
        for day in days:
            new_calendar.append(day)
    months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    #шапка календаря
    if cap == " ":
        kb.button(text=f"{cap}", callback_data="cap")
    else:
        kb.button(text=f"{cap}", callback_data="last_month")
    kb.button(text=f"{months[current_month - 1]} {current_year}", callback_data="cap") #если сюда нажмет то уведу
    kb.button(text=">", callback_data="next_month")
    #дни недели
    days_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for day_week in days_week:
        kb.button(text=day_week, callback_data=f"cap") #если сюда нажмет то уведу
    #календарь
    for day in new_calendar:
        if day == 0:
            kb.button(text=f" ", callback_data=f"cap")
        else:
            kb.button(text=f"{day}", callback_data=f"date_{day}")
    kb.adjust(3, 7, 7, 7, 7, 7, 7)
    return kb.as_markup()


# получаем нынешний месяц и выводим календарь по номеру месяца в настоящий день, далее используем calendar.Calendar().monthdaycalendar(год, месяц) - получаем список списков на каждую неделю(0=нет дня в месяце)
# current_datetime = datetime.now() ---> current_day = current_datetime.day (и так для месяца и года еще) тут получаем текущий день.мес.год


# клавиатура часов
def get_time_hour_keyboard(page=1):
    kb = InlineKeyboardBuilder()
    if page == 1:
        for i in range(0, 12):
            kb.button(text=str(i), callback_data=f"hour_{i}")
        kb.button(text=">", callback_data=f"next_hour")
    elif page == 2:
        for i in range(12, 24):
            kb.button(text=str(i), callback_data=f"hour_{i}")
        kb.button(text="<", callback_data=f"prev_hour")
    kb.adjust(3, 3, 3, 3, 2)
    return kb.as_markup()

# клавиатура минут
def get_time_minute_keyboard(hour="00"): #тут подставить выбранный час в текст, пример : 15:(текст кнопки)
    kb = InlineKeyboardBuilder()
    for i in range(0, 6):
        kb.button(text=f'{hour}:{i}0', callback_data=f"time_{hour}:{i}0")
        kb.button(text=f'{hour}:{i}5', callback_data=f"time_{hour}:{i}5")
    kb.adjust(4, 4)
    return kb.as_markup()

# клавиатура периода
def get_period_keyboard(selected=[0, 0, 0, 0, 0, 0, 0], no_period=0):
    kb = InlineKeyboardBuilder()
    for i in range(len(selected)):
        smile = ""
        if selected[i] == 1:
            smile = "✅ "
        kb.button(text=f'{smile}{days[i]}', callback_data=f"period_{i}")
    if no_period == 1:
        kb.button(text="Продолжить", callback_data=f"continue_get_period")
    else:
        kb.button(text="Не повторять", callback_data=f"no_period")
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup()

# клавиатура уведомления
def get_notification_keyboard(): # гпт советует использовать CallbackData, но я не поняла
    kb = InlineKeyboardBuilder()
    kb.button(text="🔔 10 минут", callback_data="notification_10")
    kb.button(text="⏳ 30 минут", callback_data="notification_30")
    kb.button(text="🕐 1 час", callback_data="notification_60")
    kb.button(text="🕒 2 часа", callback_data="notification_120")
    kb.button(text="🚫 Не напоминать", callback_data="no_notification")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


# -ЦЕПОЧКА ДЕЙСТВИЙ-

# добавляем имя
@main_router.message(AddTask.name)
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

    bot_msg = await message.answer("Выберите дату выполнения задачи:", reply_markup=get_date_keyboard(current_month=current_month, current_year=current_year))
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id") #получаем айди предыдущего сообщения
    await delete_last_message(last_msg_id, message)
    await state.update_data(name=name, last_msg_id=bot_msg.message_id, current_day=current_day,
                            current_month=current_month, current_year=current_year, real_current_month=real_current_month,
                            real_current_year=real_current_year, real_current_day=real_current_day)  # обновить значение(как ключ:значение) и сохранить
    await state.set_state(AddTask.date)

# добавляем дату
@main_router.message(AddTask.date)
async def get_date(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите дату с помощью кнопок ниже 👇", reply_markup=get_date_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем время
@main_router.message(AddTask.time)
async def ignore_time_text(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_time_hour_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем период
@main_router.message(AddTask.period)
async def ignore_period_text(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_period_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)

# добавляем уведомление
@main_router.message(AddTask.notification)
async def get_notification(message: Message, state: FSMContext):
    bot_msg = await message.answer(
        "Пожалуйста, выберите время с помощью кнопок ниже 👇", reply_markup=get_notification_keyboard()
    )
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    await state.update_data(last_msg_id=bot_msg.message_id)


#--УДАЛЕНИЕ--
@main_router.callback_query(F.data == "delete") #делаем клавиатуру состоящую из всех уже сохраненных задач(кол-во кнопок зависит от этого)
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

#-КЛАВИАТУРА-
def delete_task_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    for i in range(1, len(tasks[tg_id]) + 1):
        kb.button(text=f"{i}", callback_data=f"del_task_{i}")
    count = len(tasks[tg_id])
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()

def delete_issue():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="delete_yes")
    kb.button(text="❌ Нет", callback_data="delete_no")
    kb.adjust(2)
    return kb.as_markup()



#-ФУНКЦИИ КЛАВИАТУРЫ-
@main_router.callback_query(F.data.startswith("del_task_"))
async def delete(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number_task = int(call.data.split("_")[2])
    await state.update_data(number_task=number_task)
    await call.message.answer("⚠️ Вы уверены, что хотите выполнить удаление?", reply_markup=delete_issue())
    await call.answer()

@main_router.callback_query(F.data == "delete_no")
async def delete_no(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    await call.bot.delete_message(chat_id=call.message.chat.id,
                message_id=tasks_message)
    await call.message.answer("❎ Удаление отменено")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

@main_router.callback_query(F.data == "delete_yes")
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

#--ВЫВОД СПИСКА--
#конвертер периода в дни недели
def convert_selected_days_to_str(selected_days):
    result = []
    for i in range(len(selected_days)):
        if selected_days[i] == 1:
            result.append(days[i])
    return result

#--ФУНКЦИЯ ВЫВОДА--
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
            task_text = f'{idx}) {task["name"].capitalize()} - {task["date"]["day"]:02}.{task["date"]["month"]:02}.{task["date"]["year"]} в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}. {notification}'
        else:
            task_text = f'{idx}) {task["name"].capitalize()} - {task["date"]["day"]:02}.{task["date"]["month"]:02}.{task["date"]["year"]} в {task["time"]["hour"]:02}:{task["time"]["minute"]:02}. Период повторения: {period_str}'
        tasks_list.append(task_text)
    full_message = '\n\n'.join(tasks_list)
    return full_message

def output_task_week(tg_id: int): #тут будет вывод на неделю
    pass

def output_task_today(tg_id: int): #тут будет вывод на сегодня
    pass

@main_router.callback_query(F.data == "output")
async def output(call: CallbackQuery):
    await safe_delete(call.message)
    tg_id = call.from_user.id
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



#--ИЗМЕНЕНИЕ--
@main_router.callback_query(F.data == "change") #делаем клавиатуру состоящую из всех уже сохраненных задач(кол-во кнопок зависит от этого)
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

#-КЛАВИАТУРА-
def edit_task_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    for i in range(1, len(tasks[tg_id]) + 1):
        kb.button(text=f"{i}", callback_data=f"edit_task_{i}")
    count = len(tasks[tg_id])
    if count <= 4:
        kb.adjust(1)
    elif count <= 10:
        kb.adjust(2)
    else:
        kb.adjust(3)
    return kb.as_markup()

def task_change_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Название", callback_data="edit_name")
    kb.button(text="Дата", callback_data="edit_date")
    kb.button(text="Время", callback_data="edit_time")
    kb.button(text="Период", callback_data="edit_period")
    kb.button(text="Напоминание", callback_data="edit_notification")
    kb.button(text="Назад", callback_data="undo_the_change")
    kb.adjust(2, 2, 2)
    return kb.as_markup()

#-ФУНКЦИИ КЛАВИАТУРЫ-
#отмена изменения
@main_router.callback_query(F.data == "undo_the_change")
async def undo_the_change(call: CallbackQuery):
    await safe_delete(call.message)
    await call.answer("Изменение отменено!")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

#что именно меняем
@main_router.callback_query(F.data.startswith("edit_task_"))
async def edit_number_task(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number_task = int(call.data.split("_")[2])
    await state.update_data(number_task=number_task)
    await call.message.answer("Что именно в задаче вы желаете изменить?", reply_markup=task_change_keyboard())
    await call.answer()

#изменение (тут доделать само изменение)
@main_router.callback_query(F.data.startswith("edit_"))
async def edit(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    item = call.data.split("_")[1] #что именно меняем
    data = await state.get_data()
    tasks_message = data.get("tasks_message_id")
    await call.bot.delete_message(chat_id=call.message.chat.id,
                                  message_id=tasks_message)
    number_task = data.get("number_task") #номер задачи
    tg_id = call.from_user.id
    #tasks[tg_id][number_task - 1][item]

    await call.message.answer("✅ Задача успешно изменена!")
    print(tasks)
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()


#--ОЧИЩЕНИЕ--
@main_router.callback_query(F.data == "clear")
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

#-КЛАВИАТУРА-
# клавиатура подтверждения
def confirm_clear_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="clear_yes")
    kb.button(text="❌ Нет", callback_data="clear_no")
    kb.adjust(2)
    return kb.as_markup()

#-ФУНКЦИИ КЛАВИАТУРЫ-

# очистить список
@main_router.callback_query(F.data == "clear_yes")
async def confirm_clear(call: CallbackQuery):
    await safe_delete(call.message)
    tg_id = call.from_user.id
    tasks[tg_id].clear()
    await call.message.answer("🗑️ Все задачи удалены")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

# очистка списка отменена
@main_router.callback_query(F.data == "clear_no")
async def cancel_clear(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("❎ Очистка отменена")
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()


#--НАСТРОЙКИ--
@main_router.callback_query(F.data == "settings") #сортировка (по дате и времени, по названию), часовой пояс
async def settings_task(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()

#-КЛАВИАТУРЫ-

# клавиатура настроек
def settings_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📁 Сортировка", callback_data="sorting")
    kb.button(text="🕰️ Часовой пояс", callback_data="timezone")
    kb.button(text="📊 Формат вывода", callback_data="format_output")
    kb.button(text="⬅️ Назад", callback_data="cancel_setting_menu")
    kb.adjust(2, 2)
    return kb.as_markup()

#клавиатура видов сортировки
def sorting_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📁 По порядку", callback_data="sort_1")
    kb.button(text="🔤 По названию", callback_data="sort_2")
    kb.button(text="📅 По дате", callback_data="sort_3")
    kb.button(text="⏰ По времени", callback_data="sort_4")
    kb.button(text="⬅️ Назад", callback_data="cancel_setting_back")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

#клавиатура выбора часового пояса
def time_zone_keyboard():
    kb = InlineKeyboardBuilder()
    for number in ["-1", "0", "+1", "+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9"]:
        if number == "0":
            kb.button(text=f"🌍 МСК", callback_data=f"utc_{number}")
        else:
            kb.button(text=f"🌍 МСК{number}", callback_data=f"utc_{number}")
    kb.button(text="⬅️ Назад", callback_data="cancel_setting_back")
    kb.adjust(3, 3, 3, 3)
    return kb.as_markup()

#клавиатура формата вывода
def format_output_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="♾️ Все задачи", callback_data="task_1")
    kb.button(text="📅 Задачи на неделю", callback_data="task_2")
    kb.button(text="📝 Задачи на сегодня", callback_data="task_3")
    kb.button(text="⬅️ Назад", callback_data="cancel_setting_back")
    kb.adjust(2, 2)
    return kb.as_markup()

#-ФУНКЦИИ КЛАВИАТУРЫ-
#вывод задач
@main_router.callback_query(F.data.startswith ("task_")) #доделать
async def task_all(call: CallbackQuery):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    tg_id = call.from_user.id
    if settings_default[tg_id]['format_output'] == number:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=format_output_keyboard())
        return
    formats = {
        1: "все задачи",
        2: "задачи на неделю",
        3: "задачи на сегодня"
    }
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"📄 Формат вывода — {formats[number]}"
    )
    settings_default[tg_id]['format_output'] = number
    save_to_file('settings.json', settings_default)
    print(settings_default)
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

#сортировка
@main_router.callback_query(F.data.startswith ("sort_"))
async def sort_name(call: CallbackQuery):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    #сделать постоянную сортировку
    tg_id = call.from_user.id
    if settings_default[tg_id]['sort'] == number:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=sorting_keyboard())
        return
    sorts = {
        1: "по порядку",
        2: "по названию",
        3: "по дате",
        4: "по времени"
    }
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"📌 Сортировка — {sorts[number]}"
    )
    settings_default[tg_id]['sort'] = number
    save_to_file('settings.json', settings_default)
    print(settings_default)
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()


#выбор часового пояса
@main_router.callback_query(F.data.startswith ("utc_")) #тут доделать
async def utc_selection(call: CallbackQuery):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    tg_id = call.from_user.id
    if settings_default[tg_id]['timezone'] == number:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=time_zone_keyboard())
        return
    settings_default[tg_id]['timezone'] = number
    save_to_file('settings.json', settings_default)
    tz_text = f"МСК{number:+}" if number != 0 else "МСК"
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"🌍 Часовой пояс — {tz_text}"
    )
    print(settings_default)
    await call.answer()
    await call.message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())

#-ФОРМАТ ВЫВОДА-
@main_router.callback_query(F.data == "format_output")
async def format_output(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите формат вывода задач:", reply_markup=format_output_keyboard())
    await call.answer()

#-СОРТИРОВКА-
@main_router.callback_query(F.data == "sorting")
async def sorting(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите способ сортировки:", reply_markup=sorting_keyboard())
    await call.answer()

#-ЧАСОВОЙ ПОЯС-
@main_router.callback_query(F.data == "timezone")
async def time_zone(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите ваш часовой пояс:", reply_markup=time_zone_keyboard())

#-ВЕРНУТЬСЯ НАЗАД-
@main_router.callback_query(F.data.startswith("cancel_setting_menu"))
async def cancel_setting(call: CallbackQuery):
    comm = call.data.split("_")[2]
    await safe_delete(call.message)
    await call.answer("Возвращаемся назад...")
    if comm == "menu":
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    else:
        await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()


#--ЗАПУСК БОТА--
async def main():
    await set_bot_commands(bot) #задает команды для бота
    await dp.start_polling(bot) #обращается к серверу тг и проверяет на новые сообщения

if __name__ == "__main__": #если запускается из этого файла, то работает, если импортируется, то нет
    asyncio.run(main()) #запуск асинхронности