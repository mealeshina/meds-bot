import logging
from datetime import datetime


def setup_logging():
    """Настройка логирования для приложения."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=datefmt
    )

    # Дополнительно пишем в файл для отладки
    file_handler = logging.FileHandler('meds_bot.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=datefmt))
    logging.getLogger().addHandler(file_handler)

