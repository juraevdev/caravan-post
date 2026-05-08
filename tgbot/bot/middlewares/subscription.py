from aiogram import Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from django.conf import settings


class SubscriptionRequiredMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Only enforce mandatory subscription in private chat interactions.
        if isinstance(event, Message) and event.chat.type != ChatType.PRIVATE:
            return await handler(event, data)
        if isinstance(event, CallbackQuery):
            if not event.message or event.message.chat.type != ChatType.PRIVATE:
                return await handler(event, data)

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
                await self._deny(event, bot)
                return
        except (TelegramBadRequest, TelegramForbiddenError):
            await self._deny(event, bot)
            return

        return await handler(event, data)

    async def _deny(self, event, bot: Bot):
        text = "Botdan foydalanish uchun asosiy guruhimizga obuna bo'lishingiz kerak"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        join_url = await self._resolve_join_url(bot)
        if join_url:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text="Obuna bo'lish", url=join_url)]
            )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="subscription_check")]
        )

        if isinstance(event, Message):
            await event.answer(text=text, reply_markup=keyboard)
            return

        if isinstance(event, CallbackQuery):
            await event.answer("Avval guruhga qo'shiling.", show_alert=True)
            if event.message:
                await event.message.answer(text=text, reply_markup=keyboard)

    async def _resolve_join_url(self, bot: Bot) -> str:
        if settings.NEW_GROUP_LINK:
            return settings.NEW_GROUP_LINK

        try:
            chat = await bot.get_chat(settings.NEW_GROUP_ID)
            if getattr(chat, "username", None):
                return f"https://t.me/{chat.username}"
        except (TelegramBadRequest, TelegramForbiddenError):
            return ""

        return ""
