from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand
from aiogram.types import Message, CallbackQuery
from storage.tasks import tasks, settings_default
from database.db import read_from_file, save_to_file
from commands.commands_kb import timezone_keyboard
from utils.delete_last_message import delete_last_message, safe_delete
from states.auth import Auth
from keyboards.main_kb import main_menu_keyboard


commands_router = Router()
path_to_data = '/data/data.json'
path_to_settings = '/data/settings.json'

read_from_file(path_to_data, tasks)
read_from_file(path_to_settings, settings_default)


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
    if message.chat.id not in tasks:
        tasks[message.chat.id] = [] #тут сохраняется строка
        tg_id = message.from_user.id #тут сохраняется число
        settings_default[tg_id] = {'format_output': 1, 'sort': 1, 'timezone': 0}
        save_to_file(path_to_data, tasks)
        save_to_file(path_to_settings, settings_default)
        bot_msg = await message.answer("👋 Добро пожаловать!\n\nЭтот бот поможет вам планировать задачи и напоминания."
                                       "\nДля начала выберите ваш часовой пояс:", reply_markup=timezone_keyboard())
        await state.update_data(start_msg=bot_msg.message_id)
        await state.set_state(Auth.timezone)
    else:
        await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

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
    tg_id = call.from_user.id
    settings_default[tg_id]['timezone'] = number
    print(settings_default)
    save_to_file(path_to_settings, settings_default)
    await call.answer("Настройки применены!")
    await state.clear()
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())


@commands_router.message(Command("help"))
async def help(message: Message):
    await message.answer("Список доступных команд бота: \n/start\n/menu\n/help\n/settings")

@commands_router.message(Command("menu"))
async def menu(message: Message):
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

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
