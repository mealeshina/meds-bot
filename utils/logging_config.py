import logging
from datetime import datetime


def setup_logging():
    """Настройка логирования для приложения."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

