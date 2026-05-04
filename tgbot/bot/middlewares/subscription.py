from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from django.conf import settings


class SubscriptionRequiredMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        # Let user re-check membership callback even when blocked.
        if isinstance(event, CallbackQuery) and event.data == "subscription_check":
            return await handler(event, data)

        bot = data.get("bot")
        if bot is None:
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(chat_id=settings.NEW_GROUP_ID, user_id=user.id)
            if member.status in {"left", "kicked"}:
                await self._deny(event)
                return
        except (TelegramBadRequest, TelegramForbiddenError):
            await self._deny(event)
            return

        return await handler(event, data)

    async def _deny(self, event):
        text = (
            "Botdan foydalanish uchun avval majburiy guruhga qo'shiling.\n"
            "Guruh ID: "
            f"`{settings.NEW_GROUP_ID}`\n\n"
            "Guruhga qo'shilgach, \"Tekshirish\" tugmasini bosing."
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Tekshirish", callback_data="subscription_check")]
            ]
        )

        if isinstance(event, Message):
            await event.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
            return

        if isinstance(event, CallbackQuery):
            await event.answer("Avval guruhga qo'shiling.", show_alert=True)
            if event.message:
                await event.message.answer(text=text, reply_markup=keyboard, parse_mode="Markdown")
