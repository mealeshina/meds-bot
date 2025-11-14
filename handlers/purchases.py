import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services import meds_service
from utils.emojis import EMOJI_MEDICINE, EMOJI_ERROR, EMOJI_SUCCESS, EMOJI_BOX

logger = logging.getLogger(__name__)

router = Router()


class PurchaseStates(StatesGroup):
    waiting_for_medicine = State()
    waiting_for_quantity = State()


@router.message(Command("add_purchase"))
async def cmd_add_purchase(message: Message, state: FSMContext):
    """Обработчик команды /add_purchase."""
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
                    callback_data=f"purchase_med_{med['id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            f"{EMOJI_MEDICINE} Выберите лекарство, которое вы купили:",
            reply_markup=keyboard
        )
        
        await state.set_state(PurchaseStates.waiting_for_medicine)
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении покупки: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка.")
        await state.clear()


@router.callback_query(StateFilter(PurchaseStates.waiting_for_medicine), F.data.startswith("purchase_med_"))
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
        await state.set_state(PurchaseStates.waiting_for_quantity)
        
        await callback.message.edit_text(
            f"{EMOJI_BOX} Вы выбрали: <b>{medicine['name']}</b>\n\n"
            f"Введите количество купленных единиц (целое число):"
        )
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при выборе лекарства: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
        await state.clear()


@router.message(Command("cancel"), StateFilter(PurchaseStates))
async def cmd_cancel_purchase(message: Message, state: FSMContext):
    """Отмена добавления покупки."""
    await state.clear()
    await message.answer(f"{EMOJI_ERROR} Операция отменена.")


@router.message(StateFilter(PurchaseStates.waiting_for_quantity))
async def process_quantity_input(message: Message, state: FSMContext):
    """Обработка ввода количества."""
    try:
        data = await state.get_data()
        medicine_id = data.get("medicine_id")
        medicine_name = data.get("medicine_name")
        
        # Парсим количество
        try:
            quantity = int(message.text.strip())
            if quantity <= 0:
                await message.answer(f"{EMOJI_ERROR} Количество должно быть положительным числом.")
                return
        except ValueError:
            await message.answer(f"{EMOJI_ERROR} Введите целое число (например: 30)")
            return
        
        # Добавляем покупку
        new_stock = meds_service.add_purchase(medicine_id, quantity)
        
        # Получаем информацию о лекарстве для расчёта дней
        medicine = meds_service.get_medicine_by_id(medicine_id)
        daily_dose = medicine["daily_dose"]
        
        if daily_dose > 0:
            days_left = int(new_stock / daily_dose) if new_stock > 0 else 0
        else:
            days_left = 0
        
        await message.answer(
            f"{EMOJI_SUCCESS} Покупка добавлена!\n\n"
            f"Лекарство: <b>{medicine_name}</b>\n"
            f"Добавлено: <b>{quantity}</b> единиц\n"
            f"Текущий остаток: <b>{new_stock}</b> единиц\n"
            f"Хватит примерно на: <b>{days_left}</b> дней"
        )
        
        await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка при обработке количества: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при сохранении покупки.")
        await state.clear()

