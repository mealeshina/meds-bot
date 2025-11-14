import sqlite3
import logging
from config import MEDICINES_CONFIG

logger = logging.getLogger(__name__)

DB_NAME = "meds.db"


def get_connection():
    """Возвращает соединение с базой данных."""
    return sqlite3.connect(DB_NAME)


def init_db():
    """Инициализирует базу данных и создаёт таблицы, если их нет."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Создание таблицы users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER UNIQUE NOT NULL,
                first_name TEXT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Создание таблицы medicines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                latin_name TEXT NULL,
                daily_dose REAL NOT NULL,
                current_stock INTEGER NOT NULL DEFAULT 0,
                notify_before_days INTEGER NOT NULL DEFAULT 14
            )
        """)
        
        # Добавляем колонку latin_name, если её нет (для существующих БД)
        try:
            cursor.execute("ALTER TABLE medicines ADD COLUMN latin_name TEXT NULL")
            logger.info("Добавлена колонка latin_name в таблицу medicines")
        except sqlite3.OperationalError:
            # Колонка уже существует
            pass
        
        # Создание таблицы prescriptions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                expiry_date TEXT NOT NULL,
                UNIQUE(medicine_id)
            )
        """)
        
        # Создание таблицы purchases
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                purchased_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        
        # Синхронизация фиксированного списка лекарств с БД
        _sync_medicines_config(cursor, conn)
        
        logger.info("База данных инициализирована успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def _sync_medicines_config(cursor, conn):
    """Синхронизирует MEDICINES_CONFIG с таблицей medicines."""
    for med_config in MEDICINES_CONFIG:
        name = med_config["name"]
        daily_dose = med_config["daily_dose"]
        latin_name = med_config.get("latin_name")  # Необязательное поле
        
        # Проверяем, существует ли лекарство
        cursor.execute("SELECT id, daily_dose, latin_name FROM medicines WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем daily_dose и latin_name, если изменились
            med_id, old_dose, old_latin = existing
            needs_update = False
            updates = []
            
            if old_dose != daily_dose:
                updates.append(("daily_dose", daily_dose))
                needs_update = True
            
            if old_latin != latin_name:
                updates.append(("latin_name", latin_name))
                needs_update = True
            
            if needs_update:
                set_clause = ", ".join([f"{field} = ?" for field, _ in updates])
                values = [val for _, val in updates] + [med_id]
                cursor.execute(
                    f"UPDATE medicines SET {set_clause} WHERE id = ?",
                    values
                )
                logger.info(f"Обновлено лекарство {name}: {updates}")
        else:
            # Создаём новое лекарство
            cursor.execute(
                """INSERT INTO medicines (name, latin_name, daily_dose, current_stock, notify_before_days)
                   VALUES (?, ?, ?, 0, 14)""",
                (name, latin_name, daily_dose)
            )
            logger.info(f"Добавлено новое лекарство: {name} (доза: {daily_dose}, лат: {latin_name})")
    
    conn.commit()

