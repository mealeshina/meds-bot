import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services import meds_service
from utils.emojis import EMOJI_MEDICINE, EMOJI_ERROR, EMOJI_SUCCESS, EMOJI_BOX
from utils.access_control import AccessControlMiddleware

logger = logging.getLogger(__name__)

router = Router()
router.message.middleware(AccessControlMiddleware())
router.callback_query.middleware(AccessControlMiddleware())


class PurchaseStates(StatesGroup):
    waiting_for_medicine = State()
    waiting_for_quantity = State()


@router.message(Command("add_purchase"))
async def cmd_add_purchase(message: Message, state: FSMContext):
    """Обработчик команды /add_purchase."""
    try:
        logger.info(f"[add_purchase] Старт, user_id={message.from_user.id if message.from_user else None}")
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
        logger.info(f"[add_purchase] Показан список из {len(medicines)} лекарств, state=waiting_for_medicine")

    except Exception as e:
        logger.error(f"Ошибка при добавлении покупки: {e}", exc_info=True)
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка.")
        await state.clear()


@router.callback_query(StateFilter(PurchaseStates.waiting_for_medicine), F.data.startswith("purchase_med_"))
async def process_medicine_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора лекарства."""
    try:
        medicine_id = int(callback.data.split("_")[-1])
        logger.info(f"[add_purchase] Выбрано лекарство id={medicine_id}, user_id={callback.from_user.id if callback.from_user else None}")
        medicine = meds_service.get_medicine_by_id(medicine_id)
        
        if not medicine:
            await callback.answer("Лекарство не найдено", show_alert=True)
            await state.clear()
            return
        
        await state.update_data(medicine_id=medicine_id, medicine_name=medicine["name"])
        await state.set_state(PurchaseStates.waiting_for_quantity)
        
        await callback.message.edit_text(
            f"{EMOJI_BOX} Вы выбрали: <b>{medicine['name']}</b>\n\n"
            f"Введите количество (целое число):\n"
            f"• положительное — добавить к остатку\n"
            f"• отрицательное — уменьшить остаток (коррекция)"
        )
        await callback.answer()
        logger.info(f"[add_purchase] Ожидание ввода количества, state=waiting_for_quantity")

    except Exception as e:
        logger.error(f"Ошибка при выборе лекарства: {e}", exc_info=True)
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
        logger.info(f"[add_purchase] Получен ввод количества: text='{message.text}', user_id={message.from_user.id if message.from_user else None}")
        data = await state.get_data()
        medicine_id = data.get("medicine_id")
        medicine_name = data.get("medicine_name")
        
        # Парсим количество (допускаем отрицательные для коррекции)
        try:
            quantity = int(message.text.strip())
            if quantity == 0:
                await message.answer(f"{EMOJI_ERROR} Введите ненулевое число (например: 30 или -10)")
                return
        except ValueError:
            await message.answer(f"{EMOJI_ERROR} Введите целое число (например: 30 или -10)")
            return
        
        # Добавляем покупку
        logger.info(f"[add_purchase] Сохранение: medicine_id={medicine_id}, quantity={quantity}")
        new_stock = meds_service.add_purchase(medicine_id, quantity)
        
        # Получаем информацию о лекарстве для расчёта дней
        medicine = meds_service.get_medicine_by_id(medicine_id)
        daily_dose = medicine["daily_dose"]
        
        if daily_dose > 0:
            days_left = int(new_stock / daily_dose) if new_stock > 0 else 0
        else:
            days_left = 0
        
        action = "Добавлено" if quantity > 0 else "Убавлено"
        await message.answer(
            f"{EMOJI_SUCCESS} Остаток обновлён!\n\n"
            f"Лекарство: <b>{medicine_name}</b>\n"
            f"{action}: <b>{quantity:+d}</b> единиц\n"
            f"Текущий остаток: <b>{new_stock}</b> единиц\n"
            f"Хватит примерно на: <b>{days_left}</b> дней"
        )
        
        await state.clear()
        logger.info(f"[add_purchase] Покупка успешно добавлена, new_stock={new_stock}")

    except Exception as e:
        logger.error(f"Ошибка при обработке количества: {e}", exc_info=True)
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при сохранении покупки.")
        await state.clear()

