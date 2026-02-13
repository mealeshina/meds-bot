import logging
from pathlib import Path

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from utils.emojis import EMOJI_ERROR
from utils.access_control import AccessControlMiddleware

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AccessControlMiddleware())
router.callback_query.middleware(AccessControlMiddleware())

LOG_FILE = Path("meds_bot.log")
LAST_LINES = 10


@router.message(Command("logs"))
async def cmd_logs(message: Message):
    """Показать последние N записей из лога."""
    try:
        if not LOG_FILE.exists():
            await message.answer("Файл лога не найден.")
            return

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        last_lines = lines[-LAST_LINES:] if len(lines) >= LAST_LINES else lines
        text = "".join(last_lines).strip()

        if not text:
            await message.answer("Лог пуст.")
            return

        await message.answer(f"<pre>{text}</pre>")
    except Exception as e:
        logger.error(f"Ошибка при чтении лога: {e}")
        await message.answer(f"{EMOJI_ERROR} Не удалось прочитать лог.")
