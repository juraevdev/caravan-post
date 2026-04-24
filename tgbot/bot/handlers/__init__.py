from aiogram import Router

from tgbot.bot.filters import ChatPrivateFilter, IsAdminFilter


def setup_routers() -> Router:
    from .users import start, help, echo, admin, advertisement
    from .groups import forward
    from .errors import error_handler

    router = Router()

    # Agar kerak bo'lsa, o'z filteringizni o'rnating
    start.router.message.filter(ChatPrivateFilter())
    help.router.message.filter(ChatPrivateFilter())
    echo.router.message.filter(ChatPrivateFilter())
    advertisement.router.message.filter(ChatPrivateFilter())
    admin.router.message.filter(IsAdminFilter())

    router.include_routers(forward.router, admin.router, advertisement.router, start.router, help.router, 
                           echo.router, error_handler.router
                           )

    return router
