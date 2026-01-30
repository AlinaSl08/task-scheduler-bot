from aiogram.utils.keyboard import InlineKeyboardBuilder


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