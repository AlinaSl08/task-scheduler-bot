from aiogram.utils.keyboard import InlineKeyboardBuilder

def confirm_clear_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="clear_yes")
    kb.button(text="❌ Нет", callback_data="clear_no")
    kb.adjust(2)
    return kb.as_markup()