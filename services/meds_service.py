import logging
from datetime import datetime, date
from db import get_connection

logger = logging.getLogger(__name__)


def get_or_create_user(tg_user_id: int, first_name: str = None) -> int:
    """Получает или создаёт пользователя в БД. Возвращает user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE tg_user_id = ?", (tg_user_id,))
        existing = cursor.fetchone()
        
        if existing:
            user_id = existing[0]
        else:
            # Создаём нового пользователя
            created_at = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO users (tg_user_id, first_name, created_at) VALUES (?, ?, ?)",
                (tg_user_id, first_name, created_at)
            )
            user_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Создан новый пользователь: tg_user_id={tg_user_id}, user_id={user_id}")
        
        return user_id
    except Exception as e:
        logger.error(f"Ошибка при работе с пользователем: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_medicines():
    """Возвращает список всех лекарств из БД."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, latin_name, daily_dose, current_stock, notify_before_days FROM medicines ORDER BY name")
        rows = cursor.fetchall()
        
        medicines = []
        for row in rows:
            medicines.append({
                "id": row[0],
                "name": row[1],
                "latin_name": row[2],
                "daily_dose": row[3],
                "current_stock": row[4],
                "notify_before_days": row[5]
            })
        
        return medicines
    finally:
        conn.close()


def get_medicine_by_id(medicine_id: int):
    """Получает лекарство по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, name, latin_name, daily_dose, current_stock, notify_before_days FROM medicines WHERE id = ?",
            (medicine_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "latin_name": row[2],
                "daily_dose": row[3],
                "current_stock": row[4],
                "notify_before_days": row[5]
            }
        return None
    finally:
        conn.close()


def set_prescription_expiry(medicine_id: int, expiry_date: str):
    """Устанавливает или обновляет дату окончания рецепта для лекарства."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли запись
        cursor.execute("SELECT id FROM prescriptions WHERE medicine_id = ?", (medicine_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующую запись
            cursor.execute(
                "UPDATE prescriptions SET expiry_date = ? WHERE medicine_id = ?",
                (expiry_date, medicine_id)
            )
        else:
            # Создаём новую запись
            cursor.execute(
                "INSERT INTO prescriptions (medicine_id, expiry_date) VALUES (?, ?)",
                (medicine_id, expiry_date)
            )
        
        conn.commit()
        logger.info(f"Установлена дата окончания рецепта для medicine_id={medicine_id}: {expiry_date}")
    except Exception as e:
        logger.error(f"Ошибка при установке даты рецепта: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def add_purchase(medicine_id: int, quantity: int):
    """Добавляет покупку лекарства и обновляет current_stock."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем текущий остаток
        cursor.execute("SELECT current_stock FROM medicines WHERE id = ?", (medicine_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Лекарство с id={medicine_id} не найдено")
        
        current_stock = row[0]
        new_stock = max(0, current_stock + quantity)  # не уходим в минус при коррекции
        
        # Обновляем остаток
        cursor.execute(
            "UPDATE medicines SET current_stock = ? WHERE id = ?",
            (new_stock, medicine_id)
        )
        
        # Добавляем запись о покупке
        purchased_at = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO purchases (medicine_id, quantity, purchased_at) VALUES (?, ?, ?)",
            (medicine_id, quantity, purchased_at)
        )
        
        conn.commit()
        logger.info(f"Добавлена покупка: medicine_id={medicine_id}, quantity={quantity}, new_stock={new_stock}")
        
        return new_stock
    except Exception as e:
        logger.error(f"Ошибка при добавлении покупки: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_prescription_expiry(medicine_id: int):
    """Получает дату окончания рецепта для лекарства."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT expiry_date FROM prescriptions WHERE medicine_id = ?", (medicine_id,))
        row = cursor.fetchone()
        
        if row:
            return row[0]
        return None
    finally:
        conn.close()


def get_status_for_user():
    """Возвращает текстовое резюме по всем лекарствам, отсортированное по days_left (по возрастанию)."""
    medicines = get_all_medicines()
    
    status_lines = []
    for med in medicines:
        medicine_id = med["id"]
        name = med["name"]
        latin_name = med.get("latin_name")
        daily_dose = med["daily_dose"]
        current_stock = med["current_stock"]
        
        # Рассчитываем дни до окончания
        if daily_dose > 0:
            days_left = int(current_stock / daily_dose) if current_stock > 0 else 0
        else:
            days_left = 0
        
        # Получаем дату окончания рецепта
        expiry_date = get_prescription_expiry(medicine_id)
        
        status_lines.append({
            "name": name,
            "latin_name": latin_name,
            "daily_dose": daily_dose,
            "current_stock": current_stock,
            "days_left": days_left,
            "expiry_date": expiry_date
        })
    
    # Сортируем по days_left (по возрастанию - сначала те, что закончатся быстрее)
    status_lines.sort(key=lambda x: x["days_left"])
    
    return status_lines


def get_medicines_expiring_within_month():
    """Возвращает список лекарств и рецептов, которые закончатся в течение месяца."""
    from datetime import date, timedelta
    
    medicines = get_all_medicines()
    today = date.today()
    month_later = today + timedelta(days=30)
    
    expiring_items = []
    
    for med in medicines:
        medicine_id = med["id"]
        name = med["name"]
        latin_name = med.get("latin_name")
        daily_dose = med["daily_dose"]
        current_stock = med["current_stock"]
        
        # Проверяем остаток лекарства
        if daily_dose > 0:
            days_left = int(current_stock / daily_dose) if current_stock > 0 else 0
            if days_left <= 30:
                # Рассчитываем примерную дату окончания (сегодня, если уже закончилось)
                expiry_date_meds = today + timedelta(days=days_left)
                expiring_items.append({
                    "name": name,
                    "latin_name": latin_name,
                    "type": "лекарство",
                    "expiry_date": expiry_date_meds.isoformat(),
                    "days_left": days_left
                })
        
        # Проверяем рецепт
        expiry_date_str = get_prescription_expiry(medicine_id)
        if expiry_date_str:
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str).date()
                if expiry_date <= month_later:
                    days_left = (expiry_date - today).days
                    expiring_items.append({
                        "name": name,
                        "latin_name": latin_name,
                        "type": "рецепт",
                        "expiry_date": expiry_date_str,
                        "days_left": days_left
                    })
            except (ValueError, AttributeError):
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                    if expiry_date <= month_later:
                        days_left = (expiry_date - today).days
                        expiring_items.append({
                            "name": name,
                            "latin_name": latin_name,
                            "type": "рецепт",
                            "expiry_date": expiry_date_str,
                            "days_left": days_left
                        })
                except ValueError:
                    pass
    
    # Сортируем по дате окончания
    expiring_items.sort(key=lambda x: x["expiry_date"])
    
    return expiring_items


def get_all_users():
    """Возвращает список всех пользователей (для отправки напоминаний)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT tg_user_id FROM users")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def decrease_daily_stock():
    """Уменьшает остаток всех лекарств на daily_dose (ежедневная задача)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, daily_dose, current_stock FROM medicines")
        medicines = cursor.fetchall()
        
        updated_count = 0
        for med_id, name, daily_dose, current_stock in medicines:
            if daily_dose > 0:
                new_stock = max(0, int(current_stock - daily_dose))
                if new_stock != current_stock:
                    cursor.execute(
                        "UPDATE medicines SET current_stock = ? WHERE id = ?",
                        (new_stock, med_id)
                    )
                    updated_count += 1
                    logger.debug(f"Обновлён остаток для {name}: {current_stock} -> {new_stock}")
        
        conn.commit()
        logger.info(f"Ежедневное уменьшение остатков: обновлено {updated_count} лекарств")
    except Exception as e:
        logger.error(f"Ошибка при ежедневном уменьшении остатков: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

