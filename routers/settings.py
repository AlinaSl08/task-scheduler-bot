from aiogram.types import CallbackQuery
from aiogram import Router, F
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from keyboards.settings_kb import settings_menu_keyboard, sorting_keyboard, time_zone_keyboard, format_output_keyboard
from storage.tasks import settings_default
from database.db import save_to_file

settings_router = Router()

@settings_router.callback_query(F.data == "settings") #сортировка (по дате и времени, по названию), часовой пояс
async def settings_task(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()

#вывод задач
@settings_router.callback_query(F.data.startswith ("task_")) #доделать
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
    save_to_file('../settings.json', settings_default)
    print(settings_default)
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()

#сортировка
@settings_router.callback_query(F.data.startswith ("sort_"))
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
    save_to_file('../settings.json', settings_default)
    print(settings_default)
    await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await call.answer()


#выбор часового пояса
@settings_router.callback_query(F.data.startswith ("utc_")) #тут доделать
async def utc_selection(call: CallbackQuery):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    tg_id = call.from_user.id
    if settings_default[tg_id]['timezone'] == number:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=time_zone_keyboard())
        return
    settings_default[tg_id]['timezone'] = number
    save_to_file('../settings.json', settings_default)
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
@settings_router.callback_query(F.data == "format_output")
async def format_output(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите формат вывода задач:", reply_markup=format_output_keyboard())
    await call.answer()

#-СОРТИРОВКА-
@settings_router.callback_query(F.data == "sorting")
async def sorting(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите способ сортировки:", reply_markup=sorting_keyboard())
    await call.answer()

#-ЧАСОВОЙ ПОЯС-
@settings_router.callback_query(F.data == "timezone")
async def time_zone(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите ваш часовой пояс:", reply_markup=time_zone_keyboard())

#-ВЕРНУТЬСЯ НАЗАД-
@settings_router.callback_query(F.data.startswith("cancel_setting_menu"))
async def cancel_setting(call: CallbackQuery):
    comm = call.data.split("_")[2]
    await safe_delete(call.message)
    await call.answer("Возвращаемся назад...")
    if comm == "menu":
        await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    else:
        await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()

