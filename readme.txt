Основные файлы:
requirements.txt — зависимости проекта
.env.example — пример файла с токеном
config.py — конфигурация с MEDICINES_CONFIG и загрузкой токена
db.py — инициализация БД и синхронизация лекарств
main.py — точка входа (обновлён для FSM storage)

Утилиты:
utils/logging_config.py — настройка логирования

Сервисы:
services/meds_service.py — бизнес-логика работы с лекарствами
services/scheduler.py — планировщик ежедневных проверок

Обработчики:
handlers/start.py — команда /start
handlers/medicines.py — команды /meds и /medicines
handlers/prescriptions.py — команда /set_prescription (с FSM)
handlers/purchases.py — команда /add_purchase (с FSM)
handlers/status.py — команда /status

Особенности реализации
FSM для интерактивных команд — выбор лекарства через inline-кнопки
Обработка ошибок — валидация дат и чисел
Команда /cancel — отмена операций в процессе
Планировщик — ежедневные проверки в 00:00
Логирование — настройка через setup_logging()

Как запустить
Установите зависимости:
   pip install -r requirements.txt

Создайте файл .env на основе .env.example:
   BOT_TOKEN=your_actual_token_here

Настройте список лекарств в config.py (измените MEDICINES_CONFIG)

Запустите бота:
   python main.py

Команды бота
/start — регистрация и приветствие
/meds или /medicines — список всех лекарств
/status — сводка по всем лекарствам
/set_prescription — установить дату окончания рецепта
/add_purchase — добавить покупку лекарства
/cancel — отменить текущую операцию

Бот готов к использованию. При первом запуске создастся база данных meds.db с таблицами и лекарствами из MEDICINES_CONFIG.