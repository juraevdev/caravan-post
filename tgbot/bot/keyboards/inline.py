from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def channels_keyboard():
    channels = [
        "https://t.me/YukBirja_Turkmen",
        "https://t.me/JukGruz_Kazakstan",
        "https://t.me/Borkashoni_Tojikiston",
        # "https://t.me/CaravanGruz_SNG",
        # "https://t.me/GruzUkraine_Cargo",
        # "https://t.me/GruzBelarus_Cargo",
        # "https://t.me/GruzRus_Cargo",
        "https://t.me/JukGruz_KG",
    ]

    keyboard = []
    for channel in channels:
        keyboard.append(
            [InlineKeyboardButton(
                text=channel,
                callback_data=f"channel:{channel}"
            )]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def view_post_keyboard(url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 E'lonni ko‘rish", url=url)]
        ]
    )