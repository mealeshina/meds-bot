import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import Update, Message, CallbackQuery, TelegramObject
from aiogram.filters import BaseFilter

from config import ALLOWED_USER_IDS

logger = logging.getLogger(__name__)


def check_user_access(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в whitelist."""
    return user_id in ALLOWED_USER_IDS


class AccessControlFilter(BaseFilter):
    """Фильтр для проверки доступа пользователей по whitelist."""
    
    async def __call__(self, message: Message | CallbackQuery, *args, **kwargs) -> bool:
        user_id = None
        if isinstance(message, Message) and message.from_user:
            user_id = message.from_user.id
        elif isinstance(message, CallbackQuery) and message.from_user:
            user_id = message.from_user.id
        
        if user_id is None:
            return False
        
        has_access = check_user_access(user_id)
        if not has_access:
            logger.warning(f"Доступ запрещён для user_id: {user_id} (разрешённые: {ALLOWED_USER_IDS})")
        
        return has_access


class AccessControlMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователей по whitelist."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        message = None
        callback_query = None
        
        # Если это Update, извлекаем Message или CallbackQuery
        if isinstance(event, Update):
            message = event.message or event.edited_message
            callback_query = event.callback_query
        elif isinstance(event, Message):
            message = event
        elif isinstance(event, CallbackQuery):
            callback_query = event
        
        # Получаем user_id из сообщения или callback-запроса
        if message and message.from_user:
            user_id = message.from_user.id
        elif callback_query and callback_query.from_user:
            user_id = callback_query.from_user.id
        
        # Проверяем доступ только если есть user_id
        if user_id is not None:
            if not check_user_access(user_id):
                logger.warning(f"Доступ запрещён для user_id: {user_id} (разрешённые: {ALLOWED_USER_IDS})")
                
                # Получаем бота из data или из event
                bot: Bot = data.get("bot")
                if not bot and callback_query:
                    bot = callback_query.bot
                
                if bot:
                    try:
                        if message:
                            await bot.send_message(
                                chat_id=message.chat.id,
                                text="❌ Доступ запрещён. Вы не авторизованы для использования этого бота."
                            )
                        elif callback_query:
                            await callback_query.answer("❌ Доступ запрещён.", show_alert=True)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке сообщения об отказе в доступе: {e}")
                
                # Блокируем обработку - НЕ вызываем handler
                return
        
        # Если пользователь в whitelist или это не сообщение/callback, продолжаем обработку
        return await handler(event, data)
