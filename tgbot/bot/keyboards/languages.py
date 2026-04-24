from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.bot.utils.languages import AVAILABLE_LANGUAGES


def create_language_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard with language selection buttons
    
    Returns:
        InlineKeyboardMarkup: Keyboard with language buttons
    """
    keyboard = []
    
    for lang_code, lang_info in AVAILABLE_LANGUAGES.items():
        button = InlineKeyboardButton(
            text=f"{lang_info['flag']} {lang_info['name']}",
            callback_data=f"lang_{lang_code}"
        )
        keyboard.append([button])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
