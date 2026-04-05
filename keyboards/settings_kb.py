from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    kb.button(text="⬅️ Назад", callback_data="cancel_setting_back")
    kb.adjust(2, 2)
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
