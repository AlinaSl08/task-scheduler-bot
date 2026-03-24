from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from utils.delete_last_message import safe_delete
from keyboards.main_kb import main_menu_keyboard
from keyboards.settings_kb import settings_menu_keyboard, sorting_keyboard, time_zone_keyboard, format_output_keyboard
from database.database import database

settings_router = Router()

@settings_router.callback_query(F.data == "settings") #сортировка (по дате и времени, по названию), часовой пояс
async def settings_task(call: CallbackQuery):
    await safe_delete(call.message)
    await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()

#вывод задач
@settings_router.callback_query(F.data.startswith ("task_"))
async def task_all(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    format_out = database.get_format_outputs(number)
    format_id = database.get_format_outputs_id(format_out)
    setting_user = database.output_settings(user_id)[3]
    if setting_user == format_id:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=format_output_keyboard())
        return
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"📄 Формат вывода — {format_out}"
    )
    database.update_format_output_settings(user_id, format_id)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await call.answer()

#сортировка
@settings_router.callback_query(F.data.startswith ("sort_"))
async def sort_name(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    #сделать постоянную сортировку
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    format_sort = database.get_sorting(number)
    format_id = database.get_sorting_id(format_sort)
    setting_user = database.output_settings(user_id)[4]
    if setting_user == format_id:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=sorting_keyboard())
        return
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"📌 Сортировка — {format_sort}"
    )
    database.update_sorting_settings(user_id, format_id)
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)
    await call.answer()


#выбор часового пояса
@settings_router.callback_query(F.data.startswith ("utc_")) #тут доделать
async def utc_selection(call: CallbackQuery, state: FSMContext):
    await safe_delete(call.message)
    number = int(call.data.split("_")[1])
    tg_id = str(call.from_user.id)
    user_id = database.get_user_id(tg_id)
    tz_id = database.get_timezone_id(number)
    setting_user = database.output_settings(user_id)[2]
    if setting_user == tz_id:
        await call.answer("Такая настройка уже выбрана")
        await call.message.answer("Выберите действие:", reply_markup=time_zone_keyboard())
        return
    database.update_timezone_settings(user_id, tz_id)

    tz_text = f"МСК{number:+}" if number != 0 else "МСК"
    await call.message.answer(
        "⚙️ Настройки обновлены\n\n"
        "Изменено:\n"
        f"🌍 Часовой пояс — {tz_text}"
    )
    await call.answer()
    bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    await state.update_data(last_msg_id=bot_msg.message_id)

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
@settings_router.callback_query(F.data.startswith("cancel_setting_"))
async def cancel_setting(call: CallbackQuery, state: FSMContext):
    comm = call.data.split("_")[2]
    await safe_delete(call.message)
    await call.answer("Возвращаемся назад...")
    if comm == "menu":
        bot_msg = await call.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.update_data(last_msg_id=bot_msg.message_id)
    elif comm == "back":
        await call.message.answer("Выберите действие:", reply_markup=settings_menu_keyboard())
    await call.answer()



