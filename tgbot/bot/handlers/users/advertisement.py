from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from tgbot.bot.filters import ChatPrivateFilter
from tgbot.bot.utils.languages import get_text
from tgbot.bot.keyboards.languages import create_language_keyboard
from tgbot.bot.utils.ad_queue import ad_queue

# Router for advertisement handlers
router = Router()
router.message.filter(ChatPrivateFilter())

# FSM states for advertisement flow
class AdvertisementStates(StatesGroup):
    """States for advertisement creation flow"""
    selecting_language = State()
    waiting_for_ad_text = State()

# Mock channels data - replace with real channels in production
MOCK_CHANNELS = [
    {"username": "YukBirja_Turkmen", "title": "Turkmenistan"},
    {"username": "JukGruz_Kazakstan", "title": "Kazakstan"},
    {"username": "Borkashoni_Tojikiston", "title": "Tojikiston"},
    # {"username": "CaravanGruz_SNG", "title": "CaravanGruz SNG"},
    # {"username": "GruzUkraine_Cargo", "title": "GruzUkraine Cargo"},
    # {"username": "GruzBelarus_Cargo", "title": "GruzBelarus Cargo"},
    # {"username": "GruzRus_Cargo", "title": "GruzRus Cargo"},
    {"username": "JukGruz_KG", "title": "Qirg'iziston"},
    {"username": "YukMarkazi_Caravan", "title": "Yuk Markazi Caravan"},
]


def create_channels_keyboard(language_code: str) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with list of channels and view buttons
    
    Args:
        language_code: User's selected language code
    
    Returns:
        InlineKeyboardMarkup: Keyboard with channel buttons and view channel buttons
    """
    keyboard = []
    
    for channel in MOCK_CHANNELS:
        # Channel selection button
        select_button = InlineKeyboardButton(
            text=channel["title"],
            callback_data=f"channel_{channel['username']}"
        )
        # View channel button
        view_button = InlineKeyboardButton(
            text=get_text(language_code, "view_channel"),
            url=f"https://t.me/{channel['username']}"
        )
        # Add both buttons in the same row
        keyboard.append([select_button, view_button])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(Command("start"))
async def handle_start(message: Message, state: FSMContext) -> None:
    """
    Handle /start command - show language selection keyboard
    
    Args:
        message: Incoming message object
        state: FSM context for storing data
    """
    # Clear any existing state
    await state.clear()
    
    # Show language selection keyboard
    keyboard = create_language_keyboard()
    
    await message.answer(
        "🌐 Tilni tanlang / Выберите язык / Интихоби забон / Тілді таңдаңыз:",
        reply_markup=keyboard
    )
    
    # Set state to wait for language selection
    await state.set_state(AdvertisementStates.selecting_language)


@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Handle language selection from inline keyboard
    
    Args:
        callback: Callback query object
        state: FSM context for storing data
    """
    # Extract language code from callback data
    language_code = callback.data.replace("lang_", "")
    
    # Save selected language to FSM state
    await state.update_data(language=language_code)
    
    # Answer callback to remove loading state
    await callback.answer()
    
    # Show channels selection keyboard
    keyboard = create_channels_keyboard(language_code)
    
    await callback.message.answer(
        get_text(language_code, "welcome"),
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("channel_"))
async def handle_channel_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Handle channel selection from inline keyboard
    
    Args:
        callback: Callback query object
        state: FSM context for storing data
    """
    # Extract channel username from callback data
    channel_username = callback.data.replace("channel_", "")
    
    # Get user's language from FSM state
    data = await state.get_data()
    language_code = data.get("language", "uz")  # Default to Uzbek
    
    # Save selected channel to FSM state
    await state.update_data(selected_channel=channel_username)
    
    # Set state to wait for advertisement text
    await state.set_state(AdvertisementStates.waiting_for_ad_text)
    
    # Answer callback to remove loading state
    await callback.answer()
    
    # Ask user for advertisement text
    await callback.message.answer(
        get_text(language_code, "channel_selected", channel=channel_username)
    )


@router.message(AdvertisementStates.waiting_for_ad_text)
async def handle_advertisement_text(message: Message, state: FSMContext) -> None:
    """
    Handle advertisement text input and add to queue
    
    Args:
        message: Incoming message with advertisement text
        state: FSM context with stored channel data
    """
    # Get data from FSM state
    data = await state.get_data()
    channel_username = data.get("selected_channel")
    language_code = data.get("language", "uz")  # Default to Uzbek
    
    if not channel_username:
        await message.answer(get_text(language_code, "error_no_channel"))
        await state.clear()
        return
    
    try:
        # Add advertisement to queue
        ad_id = await ad_queue.add_ad(
            channel_username=channel_username,
            user_telegram_id=message.from_user.id,
            user_full_name=message.from_user.full_name,
            user_username=message.from_user.username,
            message_text=message.text,
            message_id=message.message_id  # Store original message_id for forwarding
        )
        
        # Send confirmation message to user
        await message.answer(
            f"✅ {get_text(language_code, 'ad_posted', channel=channel_username)}\n"
            f"🆔 ID: {ad_id}\n"
            f"⏰ E'lon 1 daqiqa ichida kanalga joylashtiriladi."
        )
        
        # Clear FSM state
        await state.clear()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding ad to queue for @{channel_username}: {e}")
        await message.answer(
            f"❌ Xatolik yuz berdi! E'lon @{channel_username} kanaliga qo'shilmadi.\n"
            f"Iltimos, qaytadan urinib ko'ring."
        )
        await state.clear()
