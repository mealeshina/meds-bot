import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# Whitelist разрешённых пользователей (user_id)
ALLOWED_USER_IDS = [
    199728431,
]

# Фиксированный список лекарств для мамы
# latin_name - необязательное поле, можно не указывать
MEDICINES_CONFIG = [
    {"name": "Алзепил", "latin_name": "Donepezili", "daily_dose": 1.0},
    {"name": "ПК Мерц 100", "latin_name": "Amantadini", "daily_dose": 2.0},
    {"name": "Тиаприд 100", "daily_dose": 1.5},
    {"name": "Клоназепам 2", "latin_name": "Clonazepam", "daily_dose": 0.5},
    {"name": "Мадопар 250", "latin_name": "Леводопа", "daily_dose": 8.0},
    {"name": "Мемантин", "latin_name": "Акатинол", "daily_dose": 1.0},
    {"name": "Сероквель", "latin_name": "Кветиапин", "daily_dose": 0.25},
]


class Config:
    """Класс для работы с конфигурацией бота."""
    
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        
        if not self.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN не найден в переменных окружения. "
                "Создайте файл .env и укажите BOT_TOKEN=your_token_here"
            )

