from aiogram.utils.keyboard import InlineKeyboardBuilder
import calendar

days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

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


''' 
получаем нынешний месяц и выводим календарь по номеру месяца в настоящий день, 
далее используем calendar.Calendar().monthdaycalendar(год, месяц) - получаем список списков на каждую неделю(0=нет дня в месяце)
current_datetime = datetime.now() ---> current_day = current_datetime.day (и так для месяца и года еще) тут получаем текущий день.мес.год
'''

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