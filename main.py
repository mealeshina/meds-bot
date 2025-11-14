import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from utils.logging_config import setup_logging
from utils.access_control import AccessControlMiddleware
from db import init_db
from services.scheduler import start_scheduler

from handlers import start as start_handler
from handlers import medicines as medicines_handler
from handlers import prescriptions as prescriptions_handler
from handlers import purchases as purchases_handler
from handlers import status as status_handler
from handlers import report as report_handler


async def main():
    # Загрузка и проверка конфига
    config = Config()
    setup_logging()

    # Инициализация базы данных и фиксированного списка лекарств
    init_db()

    # Создание экземпляра бота и диспетчера
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация middleware для контроля доступа
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    # Регистрация хендлеров
    dp.include_router(start_handler.router)
    dp.include_router(medicines_handler.router)
    dp.include_router(prescriptions_handler.router)
    dp.include_router(purchases_handler.router)
    dp.include_router(status_handler.router)
    dp.include_router(report_handler.router)

    # Запуск планировщика напоминаний
    await start_scheduler(bot)

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
