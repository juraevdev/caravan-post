from typing import Dict

# Language translations dictionary
TRANSLATIONS = {
    "ru": {
        "language_flag": "🇷🇺",
        "language_name": "Русский",
        "select_language": "Выберите язык:",
        "welcome": "📢 Выберите канал для публикации объявления:",
        "channel_selected": "✅ Канал выбран: @{channel}\n\n📝 Напишите ваше объявление:",
        "ad_posted": "✅ Ваше объявление опубликовано в канале @{channel}!",
        "view_ad": "🔗 Посмотреть объявление",
        "view_channel": "👁️ Посмотреть канал",
        "error_no_channel": "❌ Ошибка: Канал не выбран. Нажмите /start снова.",
        "error_post_failed": "❌ Произошла ошибка! Объявление не отправлено в канал @{channel}.\nПожалуйста, проверьте, является ли бот администратором канала.",
    },
    "uz": {
        "language_flag": "🇺🇿",
        "language_name": "O'zbekcha",
        "select_language": "Tilni tanlang:",
        "welcome": "📢 E'lon berish uchun kanalni tanlang:",
        "channel_selected": "✅ Kanal tanlandi: @{channel}\n\n📝 E'loningizni yozing:",
        "ad_posted": "✅ E'loningiz @{channel} kanaliga joylashtirildi!",
        "view_ad": "🔗 E'lonni ko'rish",
        "view_channel": "👁️ Kanalni ko'rish",
        "error_no_channel": "❌ Xatolik: Kanal tanlanmagan. Qaytadan /start ni bosing.",
        "error_post_failed": "❌ Xatolik yuz berdi! E'lon @{channel} kanaliga yuborilmadi.\nIltimos, bot kanalda admin ekanligini tekshiring.",
    },
    "tg": {
        "language_flag": "🇹🇯",
        "language_name": "Тоҷикӣ",
        "select_language": "Забонро интихоб кунед:",
        "welcome": "📢 Барои нашри эълон каналро интихоб кунед:",
        "channel_selected": "✅ Канал интихоб шуд: @{channel}\n\n📝 Эълони худро нависед:",
        "ad_posted": "✅ Эълони шумо дар канали @{channel} нашр шуд!",
        "view_ad": "🔗 Дидани эълон",
        "view_channel": "👁️ Дидани канал",
        "error_no_channel": "❌ Хатолик: Канал интихоб нашудааст. Боз /start-ро пахш кунед.",
        "error_post_failed": "❌ Хатолик рух дод! Эълон ба канали @{channel} фиристода нашуд.\nИлтимос, санҷед, ки бот дар канал администратор аст.",
    },
    "kz": {
        "language_flag": "🇰🇿",
        "language_name": "Қазақша",
        "select_language": "Тілді таңдаңыз:",
        "welcome": "📢 Жарнама жариялау үшін арнаны таңдаңыз:",
        "channel_selected": "✅ Арна таңдалды: @{channel}\n\n📝 Жарнамаңызды жазыңыз:",
        "ad_posted": "✅ Жарнамаңыз @{channel} арнасына орналастырылды!",
        "view_ad": "🔗 Жарнаманы көру",
        "view_channel": "👁️ Арнаны көру",
        "error_no_channel": "❌ Қате: Арна таңдалмаған. Қайтадан /start басыңыз.",
        "error_post_failed": "❌ Қате орын алды! Жарнама @{channel} арнасына жіберілмеді.\nӨтінемін, бот арнаның әкімші екенін тексеріңіз.",
    }
}

# Available languages
AVAILABLE_LANGUAGES = {
    "ru": {"flag": "🇷🇺", "name": "Русский"},
    "uz": {"flag": "🇺🇿", "name": "O'zbekcha"},
    "tg": {"flag": "🇹🇯", "name": "Тоҷикӣ"},
    "kz": {"flag": "🇰🇿", "name": "Қазақша"},
}

def get_text(language_code: str, key: str, **kwargs) -> str:
    """
    Get translated text by language code and key
    
    Args:
        language_code: Language code (ru, uz, tg, kz)
        key: Translation key
        **kwargs: Variables for formatting (e.g., channel="channel_name")
    
    Returns:
        str: Translated text
    """
    if language_code not in TRANSLATIONS:
        # Fallback to Uzbek if language not found
        language_code = "uz"
    
    text = TRANSLATIONS[language_code].get(key, TRANSLATIONS["uz"].get(key, key))
    
    # Format text with provided variables
    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text
