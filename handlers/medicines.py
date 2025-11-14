import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services import meds_service
from handlers.start import get_main_keyboard
from utils.emojis import EMOJI_MEDICINE, EMOJI_ERROR, EMOJI_BOX
from utils.access_control import AccessControlMiddleware

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AccessControlMiddleware())
router.callback_query.middleware(AccessControlMiddleware())


@router.message(Command("meds", "medicines"))
async def cmd_medicines(message: Message):
    """Обработчик команды /meds или /medicines."""
    try:
        medicines = meds_service.get_all_medicines()
        
        if not medicines:
            await message.answer(f"{EMOJI_BOX} Список лекарств пуст.")
            return
        
        text_lines = [f"{EMOJI_MEDICINE} <b>Список лекарств:</b>\n"]
        
        for med in medicines:
            medicine_id = med["id"]
            name = med["name"]
            latin_name = med.get("latin_name")
            daily_dose = med["daily_dose"]
            current_stock = med["current_stock"]
            
            # Рассчитываем дни до окончания
            if daily_dose > 0:
                days_left = int(current_stock / daily_dose) if current_stock > 0 else 0
            else:
                days_left = 0
            
            # Получаем дату окончания рецепта
            expiry_date = meds_service.get_prescription_expiry(medicine_id)
            
            # Формируем название с латинским названием, если есть
            if latin_name:
                text_lines.append(f"<b>{name}</b> ({latin_name})")
            else:
                text_lines.append(f"<b>{name}</b>")
            
            text_lines.append(f"  Доза в день: {daily_dose}")
            text_lines.append(f"  Остаток: {current_stock} единиц")
            text_lines.append(f"  Хватит примерно на: {days_left} дней")
            
            if expiry_date:
                text_lines.append(f"  Рецепт до: {expiry_date}")
            else:
                text_lines.append(f"  Рецепт: не задан")
            
            text_lines.append("")
        
        response_text = "\n".join(text_lines)
        await message.answer(response_text, reply_markup=get_main_keyboard())
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка лекарств: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при получении списка лекарств.")

