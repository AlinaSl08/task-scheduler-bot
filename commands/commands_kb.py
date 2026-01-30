from aiogram.utils.keyboard import InlineKeyboardBuilder

#клавиатура часового пояса в начале
def timezone_keyboard():
    kb = InlineKeyboardBuilder()
    for number in ["-1", "0", "+1", "+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9"]:
        if number == "0":
            kb.button(text=f"🌍 МСК", callback_data=f"default_utc_{number}")
        else:
            kb.button(text=f"🌍 МСК{number}", callback_data=f"default_utc_{number}")
    kb.adjust(3, 3, 3, 2)
    return kb.as_markup()