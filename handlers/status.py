import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services import meds_service
from handlers.start import get_main_keyboard
from utils.emojis import EMOJI_STATUS, EMOJI_MEDICINE, EMOJI_ERROR, EMOJI_BOX
from utils.access_control import AccessControlMiddleware

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AccessControlMiddleware())
router.callback_query.middleware(AccessControlMiddleware())


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Обработчик команды /status."""
    try:
        status_data = meds_service.get_status_for_user()
        
        if not status_data:
            await message.answer(f"{EMOJI_BOX} Нет данных о лекарствах.")
            return
        
        text_lines = [f"{EMOJI_STATUS} <b>Сводка по лекарствам:</b>\n"]
        
        for item in status_data:
            # Формируем название с латинским названием, если есть
            latin_name = item.get('latin_name')
            if latin_name:
                text_lines.append(f"{EMOJI_MEDICINE} <b>{item['name']}</b> ({latin_name})")
            else:
                text_lines.append(f"{EMOJI_MEDICINE} <b>{item['name']}</b>")
            
            text_lines.append(f"  Доза в день: {item['daily_dose']}")
            text_lines.append(f"  Остаток: {item['current_stock']} единиц")
            text_lines.append(f"  Хватит примерно на: {item['days_left']} дней")
            
            if item['expiry_date']:
                text_lines.append(f"  Рецепт до: {item['expiry_date']}")
            else:
                text_lines.append(f"  Рецепт: не задан")
            
            text_lines.append("")
        
        response_text = "\n".join(text_lines)
        await message.answer(response_text, reply_markup=get_main_keyboard())
    
    except Exception as e:
        logger.error(f"Ошибка при получении статуса: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при получении статуса.")

