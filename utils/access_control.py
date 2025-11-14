import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from config import ALLOWED_USER_IDS

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователей по whitelist."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        
        # Проверяем сообщения и callback-запросы от пользователей
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id is not None:
            # Проверяем, есть ли user_id в whitelist
            if user_id not in ALLOWED_USER_IDS:
                logger.warning(f"Доступ запрещён для user_id: {user_id}")
                if isinstance(event, Message):
                    await event.answer("❌ Доступ запрещён. Вы не авторизованы для использования этого бота.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Доступ запрещён.", show_alert=True)
                return
        
        # Если пользователь в whitelist или это не сообщение/callback, продолжаем обработку
        return await handler(event, data)

