from django.conf import settings
from tgbot.models import BotAdmin
from asgiref.sync import sync_to_async
from django.db.utils import OperationalError, ProgrammingError
import logging


logger = logging.getLogger(__name__)


async def get_admins():
    ADMINS = []
    ADMINS += settings.ADMINS

    try:
        BOT_ADMINS = await sync_to_async(
            lambda: list(BotAdmin.objects.filter(is_active=True).values_list('user__telegram_id', flat=True)),
            thread_sensitive=True
        )()
        ADMINS += BOT_ADMINS
    except (ProgrammingError, OperationalError) as error:
        # DB schema may be incomplete during first deploy; keep bot alive with env admins only.
        logger.warning("Could not load BotAdmin records, falling back to settings.ADMINS only: %s", error)

    return ADMINS
