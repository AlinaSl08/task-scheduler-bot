from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand
from aiogram.types import Message, CallbackQuery
from storage.tasks import tasks, settings_default
from database.db import read_from_file, save_to_file
from commands.commands_kb import timezone_keyboard, report_keyboard
from utils.delete_last_message import delete_last_message, safe_delete
from states.auth import Auth
from states.menu import Menu
from keyboards.main_kb import main_menu_keyboard
import datetime
import os
import pymorphy3

morph = pymorphy3.MorphAnalyzer()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Базовый путь к папке data
# На Amvera это будет /data, локально - data
DATA_DIR = os.path.join(BASE_DIR, "data")

# Путь к конкретному файлу
DATA_FILE_PATH = os.path.join(DATA_DIR, "data.json")
SETTINGS_FILE_PATH = os.path.join(DATA_DIR, "settings.json")


commands_router = Router()
#DATA_FILE_PATH = 'data/data.json'
#SETTINGS_FILE_PATH = 'data/settings.json'
os.makedirs(DATA_DIR, exist_ok=True)


read_from_file(DATA_FILE_PATH, tasks)
read_from_file(SETTINGS_FILE_PATH, settings_default)


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

@commands_router.message(Command("start"))
async def start(message: Message, state: FSMContext): #обозначаем что мы дадим в функцию(какой тип данных)
    user_id = str(message.chat.id)
    if user_id not in tasks:
        tasks[user_id] = [] #тут сохраняется строка
        settings_default[user_id] = {'format_output': 1, 'sort': 1, 'timezone': 0}
        save_to_file(DATA_FILE_PATH, tasks)
        save_to_file(SETTINGS_FILE_PATH, settings_default)
        bot_msg = await message.answer("👋 Добро пожаловать!\n\nЭтот бот поможет вам планировать задачи и напоминания."
                                       "\nДля начала выберите ваш часовой пояс:", reply_markup=timezone_keyboard())
        await state.update_data(start_msg=bot_msg.message_id)
        await state.set_state(Auth.timezone)
        #await state.set_state(Menu.menu)
    else:
        bot_msg = await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.set_state(Menu.menu)
        await state.update_data(last_msg_id=bot_msg.message_id)





@commands_router.message(Auth.timezone)
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



#сохранение часового пояса по умолчанию
@commands_router.callback_query(F.data.startswith ("default_utc_"))
async def utc_selection_default(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number = int(call.data.split("_")[2])
    tg_id = str(call.from_user.id)
    settings_default[tg_id]['timezone'] = number
    print(settings_default)
    save_to_file(SETTINGS_FILE_PATH, settings_default)
    await call.answer("Настройки применены!")
    await state.set_state(Menu.menu)
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())


@commands_router.message(Command("help"))
async def help(message: Message):
    await message.answer("🤖 Список доступных команд бота: \n/start\n/menu\n/help\n/settings\n/report")

@commands_router.message(Command("menu"))
async def menu(message: Message, state: FSMContext):
    bot_msg = await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.set_state(Menu.menu)
    await state.update_data(last_msg_id=bot_msg.message_id)

def settings_output(tg_id):
    tz = settings_default[tg_id]['timezone']
    srt = settings_default[tg_id]['sort']
    form_out = settings_default[tg_id]['format_output']
    return (f'⚙️ Ваши настройки:\n\n🌍 Часовой пояс: {settings_transcript["timezone"][tz]}\n'
            f'📌 Сортировка: {settings_transcript["sort"][srt]}\n'
            f'📄 Формат вывода задач: {settings_transcript["format_output"][form_out]}\n'
            f'\nЧтобы изменить параметры, откройте раздел «Настройки» в главном меню.')


#вывод настроек пользователя
@commands_router.message(Command("settings"))
async def settings(message: Message):
    tg_id = str(message.from_user.id)
    await message.answer(settings_output(tg_id))
    await message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())

#склоняет текст
def get_word(word, count):
    # Находит слово и согласует его с числом
    return morph.parse(word)[0].make_agree_with_number(count).word

def get_done_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return "выполнена"
    return "выполнены"

def get_expired_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return "просрочена"
    return "просрочены"

@commands_router.callback_query(F.data.endswith("_week"))
async def report_tasks_by_week(call: CallbackQuery):
    result = call.data.split("_")[0]
    await safe_delete(call.message)
    tg_id = str(call.from_user.id)
    current_date = datetime.date.today() #сегодняшняя дата
    days_till_monday = datetime.date.weekday(current_date)
    count_completed = 0
    count_expired = 0
    for task in tasks[tg_id]:
        day = task["date"]["day"]
        month = task["date"]["month"]
        year = task["date"]["year"]
        completed = task["completed"]
        hour = task['time']["hour"]
        minute = task['time']["minute"]
        task_datetime = datetime.datetime(year, month, day, hour, minute)
        now = datetime.datetime.now()
        task_date = datetime.date(day=day, month=month, year=year) #дата задачи
        if result == "this":
            date_monday = current_date - datetime.timedelta(days=days_till_monday)  # дата прошлого понедельника
            if task_date >= date_monday and completed:
                count_completed += 1
            elif task_date >= date_monday and task_datetime < now and not completed:
                count_expired += 1
        else:
            date_last_monday = current_date - datetime.timedelta(days=days_till_monday) - datetime.timedelta(days=7) # дата позапрошлого понедельника
            if task_date >= date_last_monday and completed:
                count_completed += 1
            elif task_date >= date_last_monday and task_datetime < now and not completed:
                count_expired += 1
    if result == "this":
        await call.message.answer(f'📊 Статистика задач:\n\n✅ {get_done_word(count_completed).capitalize()} на этой неделе {count_completed} {get_word("задача", count_completed)}!'
                                  f'\n⚠️ {get_expired_word(count_expired).capitalize()} на этой неделе {count_expired} {get_word("задача", count_expired)}!')
    else:
        await call.message.answer(f'📊 Статистика задач:\n\n✅ {get_done_word(count_completed).capitalize()} {count_completed} {get_word("задача", count_completed)} с прошлой недели!'
                                  f'\n⚠️ {get_expired_word(count_expired).capitalize()} {count_expired} {get_word("задача", count_expired)} с прошлой недели!')
    await call.message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())
    await call.answer()

@commands_router.callback_query(F.data == "general")
async def report_tasks(call: CallbackQuery):
    await safe_delete(call.message)
    count_completed = 0
    count_expired = 0
    tg_id = str(call.from_user.id)
    for task in tasks[tg_id]:
        completed = task["completed"]
        if completed:
            count_completed += 1
        else:
            count_expired += 1
    await call.message.answer(
        f'📊 Статистика задач:\n\n✅ Всего {get_done_word(count_completed)} {count_completed} {get_word("задача", count_completed)}!'
        f'\n⚠️ Всего {get_expired_word(count_expired)} {count_expired} {get_word("задача", count_expired)}!')
    await call.message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())
    await call.answer()

@commands_router.callback_query(F.data == "back")
async def report_cancel(call: CallbackQuery):
    await safe_delete(call.message)
    await call.answer("Возвращаемся назад...")
    await call.message.answer("Добро пожаловать в чат-бота!", reply_markup=main_menu_keyboard())
    await call.answer()




#отчет по выполненным и просроченным задачам
@commands_router.message(Command("report")) #если пишет текстом, нужно уведа
async def report(message: Message):
    await message.answer("Какой отчет желаете получить?", reply_markup=report_keyboard())



# создание подсказать к командам при вводе /
async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Показать меню"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="settings", description="Активные настройки"),
        BotCommand(command="report", description="Отчет по выполненным задачам")
    ]
    await bot.set_my_commands(commands) # отправляем телеграм список команд бота




@commands_router.message(F.text)
async def ignore_menu(message: Message, state: FSMContext):
    current_state = await state.get_state()
    # Если пользователь находится в состоянии меню
    if current_state == Menu.menu.state:
        data = await state.get_data()
        menu_msg_id = data.get("last_msg_id")
        # Удаляем старое сообщение бота
        if menu_msg_id:
            await delete_last_message(menu_msg_id, message)
        bot_msg = await message.answer(
            "Пожалуйста, выберите действие с помощью кнопок ниже 👇", reply_markup=main_menu_keyboard()
        )
        # Сохраняем новый id
        await state.update_data(last_msg_id=bot_msg.message_id)