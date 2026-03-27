from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand
from aiogram.types import Message, CallbackQuery
from commands.commands_kb import timezone_keyboard, report_keyboard
from utils.delete_last_message import delete_last_message, safe_delete
from states.auth_state import Auth
from states.menu_state import Menu
from keyboards.main_kb import main_menu_keyboard
import datetime
import os
import pymorphy3
from database.database import database

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


#read_from_file(DATA_FILE_PATH, tasks)
#read_from_file(SETTINGS_FILE_PATH, settings_default)


timezone_transcript = {-1: "МСК-1", 0: "МСК", 1: "МСК+1", 2: "МСК+2", 3: "МСК+3", 4: "МСК+4",
        5: "МСК+5", 6: "МСК+6", 7: "МСК+7", 8: "МСК+8", 9: "МСК+9"}


@commands_router.message(Command("start"))
async def start(message: Message, state: FSMContext): #обозначаем что мы дадим в функцию(какой тип данных)
    user_id = int(message.chat.id)
    if not database.is_exist_user(user_id):
        database.add_new_user(user_id)
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
    user_id = database.get_user_id(tg_id)
    timezone_id = database.get_timezone_id(number)
    database.set_default_settings(user_id, timezone_id) #установка дефолтных настроек
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
    user_id = database.get_user_id(tg_id)
    settings_tuple = database.output_settings(user_id)
    tz = settings_tuple[2]
    form_out = settings_tuple[3]
    srt = settings_tuple[4]
    timezone = database.get_timezone(tz)
    format_output = database.get_format_outputs(form_out)
    sorting = database.get_sorting(srt)
    return (f'⚙️ Ваши настройки:\n\n🌍 Часовой пояс: {timezone_transcript[timezone]}\n'
            f'📌 Сортировка: {sorting}\n'
            f'📄 Формат вывода задач: {format_output}\n'
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
    await call.answer()
    result = call.data.split("_")[0]
    await safe_delete(call.message)
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id) #список всех задач юзера
    current_date = datetime.datetime.now()  # сегодняшняя дата и время
    days_till_monday = datetime.date.weekday(current_date)  # дата понедельника
    count_completed = 0
    count_expired = 0
    for task in tasks_list:
        task_date = task[2] #дата задачи
        completed = task[5] #выполнено или нет
        task_time = task[3] #время задачи
        task_datetime = datetime.datetime.combine(task_date, datetime.time.min) + task_time #дата и время задачи
        if result == "this":
            date_monday = current_date - datetime.timedelta(days=days_till_monday)  # дата прошлого понедельника
            if task_datetime >= date_monday and completed:
                count_completed += 1
            elif current_date > task_datetime >= date_monday and str(completed) == '0': #если дата уже прошла и не выполнена, то ставим просрочено
                count_expired += 1
        else:
            date_last_monday = current_date - datetime.timedelta(days=days_till_monday) - datetime.timedelta(days=7) # дата позапрошлого понедельника
            if task_datetime >= date_last_monday and completed:
                count_completed += 1
            elif current_date > task_datetime >= date_last_monday and str(completed) == '0':
                count_expired += 1
    if result == "this":
        await call.message.answer(f'📊 Статистика задач:\n\n✅ {get_done_word(count_completed).capitalize()} на этой неделе {count_completed} {get_word("задача", count_completed)}!'
                                      f'\n⚠️ {get_expired_word(count_expired).capitalize()} на этой неделе {count_expired} {get_word("задача", count_expired)}!')
    else:
        await call.message.answer(f'📊 Статистика задач:\n\n✅ {get_done_word(count_completed).capitalize()} {count_completed} {get_word("задача", count_completed)} с прошлой недели!'
                                      f'\n⚠️ {get_expired_word(count_expired).capitalize()} {count_expired} {get_word("задача", count_expired)} с прошлой недели!')


@commands_router.callback_query(F.data == "report_general")
async def report_tasks(call: CallbackQuery):
    await safe_delete(call.message)
    count_completed = 0
    count_expired = 0
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    for task in tasks_list:
        completed = task[5]
        if completed:
            count_completed += 1
        elif str(completed) == '0':
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
async def report(message: Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    user_id = database.get_user_id(tg_id)
    tasks_list = database.get_all_tasks(user_id)
    if tasks_list: #если задачи есть
        await message.answer("Какой отчет желаете получить?", reply_markup=report_keyboard())
    else:
        await message.answer("Еще не было добавлено ни одной задачи!")
        bot_msg = await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.set_state(Menu.menu)
        await state.update_data(last_msg_id=bot_msg.message_id)

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