import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services import meds_service
from utils.emojis import (
    BUTTON_STATUS, BUTTON_ADD_PURCHASE,
    BUTTON_SET_PRESCRIPTION, BUTTON_REPORT,
    EMOJI_HELLO, EMOJI_ERROR, EMOJI_DOWN
)

logger = logging.getLogger(__name__)

router = Router()


def get_main_keyboard():
    """Создаёт основную клавиатуру с кнопками навигации."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUTTON_STATUS)
            ],
            [
                KeyboardButton(text=BUTTON_ADD_PURCHASE),
                KeyboardButton(text=BUTTON_SET_PRESCRIPTION)
            ],
            [
                KeyboardButton(text=BUTTON_REPORT)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Регистрируем пользователя
    try:
        meds_service.get_or_create_user(user_id, first_name)
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        await message.answer(f"{EMOJI_ERROR} Произошла ошибка при регистрации. Попробуйте позже.")
        return
    
    welcome_text = (
        f"{EMOJI_HELLO} Привет! Я бот для отслеживания лекарств для мамы.\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Отслеживать остатки лекарств\n"
        "• Отслеживать сроки действия рецептов\n"
        "• Присылать напоминания:\n"
        "  - за месяц до окончания рецепта\n"
        "  - за две недели до окончания лекарств\n\n"
        "📝 <b>Доступные команды:</b>\n"
        "/meds - показать список всех лекарств\n"
        "/status - показать запас наличия\n"
        "/set_prescription - установить дату окончания рецепта\n"
        "/add_purchase - добавить покупку лекарства\n"
        "/report - ближайшие закупки\n\n"
        f"Или используйте кнопки ниже {EMOJI_DOWN}"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(F.text == BUTTON_STATUS)
async def cmd_status_button(message: Message):
    """Обработчик кнопки 'Статус'."""
    from handlers import status as status_handler
    await status_handler.cmd_status(message)


@router.message(F.text == BUTTON_ADD_PURCHASE)
async def cmd_add_purchase_button(message: Message, state: FSMContext):
    """Обработчик кнопки 'Добавить покупку'."""
    from handlers import purchases as purchases_handler
    await purchases_handler.cmd_add_purchase(message, state)


@router.message(F.text == BUTTON_SET_PRESCRIPTION)
async def cmd_set_prescription_button(message: Message, state: FSMContext):
    """Обработчик кнопки 'Установить рецепт'."""
    from handlers import prescriptions as prescriptions_handler
    await prescriptions_handler.cmd_set_prescription(message, state)


@router.message(F.text == BUTTON_REPORT)
async def cmd_report_button(message: Message):
    """Обработчик кнопки 'Ближайшие закупки'."""
    from handlers import report as report_handler
    await report_handler.cmd_report(message)

