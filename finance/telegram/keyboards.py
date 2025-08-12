from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Создает клавиатуру с основными командами"""
    buttons = [
        [KeyboardButton(text="/today"), KeyboardButton(text="/week")],
        [KeyboardButton(text="/add"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/menu")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_remove_keyboard():
    """Клавиатура для удаления текущей клавиатуры"""
    return ReplyKeyboardRemove()