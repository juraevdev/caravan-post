import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from src.settings import FORWARD_QUEUE_MAXSIZE, FORWARD_WORKERS, NEW_GROUP_ID, OLD_GROUP_ID

router = Router()
logger = logging.getLogger(__name__)


@dataclass
class ForwardTask:
    chat_id: int
    message_id: int


forward_queue: asyncio.Queue[ForwardTask] = asyncio.Queue(maxsize=FORWARD_QUEUE_MAXSIZE)
worker_tasks: list[asyncio.Task] = []


@router.message(F.chat.id == OLD_GROUP_ID)
async def enqueue_forward(message: types.Message) -> None:
    task = ForwardTask(chat_id=message.chat.id, message_id=message.message_id)
    try:
        forward_queue.put_nowait(task)
    except asyncio.QueueFull:
        logger.warning(
            "Forward queue is full (%s). Dropping message %s from %s.",
            FORWARD_QUEUE_MAXSIZE,
            message.message_id,
            message.chat.id,
        )


async def _copy_with_retry(bot: Bot, task: ForwardTask, retries: int = 3) -> bool:
    for attempt in range(1, retries + 1):
        try:
            await bot.copy_message(
                chat_id=NEW_GROUP_ID,
                from_chat_id=task.chat_id,
                message_id=task.message_id,
            )
            return True
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 0.1)
        except TelegramAPIError as exc:
            # Transient telegram API/network issues should retry, permanent ones should stop quickly.
            if attempt == retries:
                logger.error(
                    "Failed to forward message %s after %s attempts: %s",
                    task.message_id,
                    retries,
                    exc,
                )
                return False
            await asyncio.sleep(min(2**attempt, 5))
    return False


async def _forward_worker(bot: Bot, worker_id: int) -> None:
    logger.info("Forward worker %s started", worker_id)
    while True:
        task: Optional[ForwardTask] = None
        try:
            task = await forward_queue.get()
            await _copy_with_retry(bot=bot, task=task)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Unexpected forward worker error: %s", exc)
        finally:
            if task is not None:
                forward_queue.task_done()
    logger.info("Forward worker %s stopped", worker_id)


async def start_forward_workers(bot: Bot) -> None:
    if worker_tasks:
        return

    for idx in range(FORWARD_WORKERS):
        worker_tasks.append(asyncio.create_task(_forward_worker(bot=bot, worker_id=idx + 1)))
    logger.info(
        "Forward workers started. old_group=%s, new_group=%s, workers=%s, queue=%s",
        OLD_GROUP_ID,
        NEW_GROUP_ID,
        FORWARD_WORKERS,
        FORWARD_QUEUE_MAXSIZE,
    )


async def stop_forward_workers() -> None:
    if not worker_tasks:
        return

    for task in worker_tasks:
        task.cancel()
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    worker_tasks.clear()
