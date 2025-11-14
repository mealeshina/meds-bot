import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services import meds_service
from handlers.start import get_main_keyboard
from utils.emojis import EMOJI_REPORT, EMOJI_MEDICINE, EMOJI_PRESCRIPTION, EMOJI_SUCCESS, EMOJI_ERROR

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("report"))
async def cmd_report(message: Message):
    """Обработчик команды /report - отчёт по лекарствам/рецептам, которые закончатся в течение месяца."""
    try:
        expiring_items = meds_service.get_medicines_expiring_within_month()
        
        if not expiring_items:
            await message.answer(f"{EMOJI_SUCCESS} Нет лекарств или рецептов, которые закончатся в течение месяца.")
            return
        
        text_lines = [f"{EMOJI_REPORT} <b>Отчёт: что закончится в течение месяца</b>\n"]
        
        for item in expiring_items:
            name = item["name"]
            latin_name = item.get("latin_name")
            item_type = item["type"]
            expiry_date_str = item["expiry_date"]
            days_left = item["days_left"]
            
            # Форматируем дату для отображения
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str).date()
                formatted_date = expiry_date.strftime("%d.%m.%Y")
            except (ValueError, AttributeError):
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                    formatted_date = expiry_date.strftime("%d.%m.%Y")
                except ValueError:
                    formatted_date = expiry_date_str
            
            # Формируем название с латинским названием, если есть
            if latin_name:
                name_display = f"{name} ({latin_name})"
            else:
                name_display = name
            
            if item_type == "лекарство":
                text_lines.append(f"{EMOJI_MEDICINE} {name_display} - {formatted_date}")
            else:  # рецепт
                text_lines.append(f"{EMOJI_PRESCRIPTION} {name_display} - {formatted_date}")
        
        response_text = "\n".join(text_lines)
        await message.answer(response_text, reply_markup=get_main_keyboard())
    
    except Exception as e:
        logger.error(f"Ошибка при получении отчёта: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при получении отчёта.")

