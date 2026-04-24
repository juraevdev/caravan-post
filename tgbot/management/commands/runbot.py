import asyncio
import logging
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
from tgbot.bot.loader import dp, bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run bot in polling'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bot started!"))
        try:
            main()
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("Bot stopped!"))


def setup_handlers(dispatcher: Dispatcher) -> None:
    """HANDLERS"""
    from tgbot.bot.handlers import setup_routers

    dispatcher.include_router(setup_routers())


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    from tgbot.bot.middlewares.throttling import ThrottlingMiddleware

    # Spamdan himoya qilish uchun klassik ichki o'rta dastur. So'rovlar orasidagi asosiy vaqtlar 0,5 soniya
    dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))


def setup_filters(dispatcher: Dispatcher) -> None:
    """FILTERS"""
    # Keep global filters empty so group-level handlers can receive updates.
    # Private chat filters are applied per-router in handlers/__init__.py.
    return


async def setup_aiogram(dispatcher: Dispatcher, bot: Bot) -> None:
    logger.info("Configuring aiogram")
    setup_handlers(dispatcher=dispatcher)
    setup_middlewares(dispatcher=dispatcher, bot=bot)
    setup_filters(dispatcher=dispatcher)
    logger.info("Configured aiogram")


async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    from tgbot.bot.utils.set_bot_commands import set_default_commands
    from tgbot.bot.utils.notify_admins import on_startup_notify
    from tgbot.bot.handlers.groups.forward import start_forward_workers

    logger.info("Starting polling")
    await bot.delete_webhook(drop_pending_updates=True) # False bo'lsa bot o'chgan vaqtdagi xabarlarga ham javob beradi

    await setup_aiogram(bot=bot, dispatcher=dispatcher)
    await on_startup_notify(bot=bot)
    await set_default_commands(bot=bot)
    await start_forward_workers(bot=bot)


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot):
    from tgbot.bot.handlers.groups.forward import stop_forward_workers

    logger.info("Stopping polling")
    await stop_forward_workers()
    await bot.session.close()
    await dispatcher.storage.close()


def main():
    """CONFIG"""
    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dp.start_polling(bot, close_bot_session=True, allowed_updates=["message"]))
