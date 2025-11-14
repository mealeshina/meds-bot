import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services import meds_service
from utils.emojis import EMOJI_MEDICINE, EMOJI_ERROR, EMOJI_SUCCESS, EMOJI_BOX, EMOJI_CALENDAR
from utils.access_control import AccessControlMiddleware

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AccessControlMiddleware())
router.callback_query.middleware(AccessControlMiddleware())


class PrescriptionStates(StatesGroup):
    waiting_for_medicine = State()
    waiting_for_date = State()


@router.message(Command("set_prescription"))
async def cmd_set_prescription(message: Message, state: FSMContext):
    """Обработчик команды /set_prescription."""
    try:
        medicines = meds_service.get_all_medicines()
        
        if not medicines:
            await message.answer(f"{EMOJI_BOX} Список лекарств пуст.")
            return
        
        # Создаём inline-клавиатуру с лекарствами
        keyboard_buttons = []
        for med in medicines:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=med["name"],
                    callback_data=f"presc_med_{med['id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            f"{EMOJI_MEDICINE} Выберите лекарство, для которого хотите установить дату окончания рецепта:",
            reply_markup=keyboard
        )
        
        await state.set_state(PrescriptionStates.waiting_for_medicine)
    
    except Exception as e:
        logger.error(f"Ошибка при установке рецепта: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка.")
        await state.clear()


@router.callback_query(StateFilter(PrescriptionStates.waiting_for_medicine), F.data.startswith("presc_med_"))
async def process_medicine_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора лекарства."""
    try:
        medicine_id = int(callback.data.split("_")[-1])
        medicine = meds_service.get_medicine_by_id(medicine_id)
        
        if not medicine:
            await callback.answer("Лекарство не найдено", show_alert=True)
            await state.clear()
            return
        
        await state.update_data(medicine_id=medicine_id, medicine_name=medicine["name"])
        await state.set_state(PrescriptionStates.waiting_for_date)
        
        await callback.message.edit_text(
            f"{EMOJI_CALENDAR} Вы выбрали: <b>{medicine['name']}</b>\n\n"
            f"Введите дату окончания рецепта в формате <b>ДД.ММ.ГГГГ</b>\n"
            f"Например: 31.12.2024"
        )
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при выборе лекарства: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
        await state.clear()


@router.message(Command("cancel"), StateFilter(PrescriptionStates))
async def cmd_cancel_prescription(message: Message, state: FSMContext):
    """Отмена установки рецепта."""
    await state.clear()
    await message.answer(f"{EMOJI_ERROR} Операция отменена.")


@router.message(StateFilter(PrescriptionStates.waiting_for_date))
async def process_date_input(message: Message, state: FSMContext):
    """Обработка ввода даты."""
    try:
        data = await state.get_data()
        medicine_id = data.get("medicine_id")
        medicine_name = data.get("medicine_name")
        
        date_str = message.text.strip()
        
        # Парсим дату в формате ДД.ММ.ГГГГ
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
            expiry_date_iso = date_obj.isoformat()  # YYYY-MM-DD
        except ValueError:
            await message.answer(
                f"{EMOJI_ERROR} Неверный формат даты. Используйте формат <b>ДД.ММ.ГГГГ</b>\n"
                "Например: 31.12.2024"
            )
            return
        
        # Сохраняем дату в БД
        meds_service.set_prescription_expiry(medicine_id, expiry_date_iso)
        
        await message.answer(
            f"{EMOJI_SUCCESS} Рецепт установлен!\n\n"
            f"Лекарство: <b>{medicine_name}</b>\n"
            f"Дата окончания: <b>{date_str}</b>"
        )
        
        await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка при обработке даты: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при сохранении рецепта.")
        await state.clear()

