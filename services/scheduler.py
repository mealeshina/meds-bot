import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from services import meds_service
from utils.emojis import EMOJI_REMINDER_PRESCRIPTION, EMOJI_REMINDER_MEDICINE

logger = logging.getLogger(__name__)

scheduler = None


async def check_prescriptions(bot: Bot):
    """Проверяет рецепты и отправляет напоминания за 30 дней до окончания."""
    try:
        medicines = meds_service.get_all_medicines()
        today = date.today()
        users = meds_service.get_all_users()
        
        if not users:
            logger.info("Нет зарегистрированных пользователей для отправки напоминаний")
            return
        
        for med in medicines:
            medicine_id = med["id"]
            expiry_date_str = meds_service.get_prescription_expiry(medicine_id)
            
            if not expiry_date_str:
                continue
            
            # Парсим дату окончания
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str).date()
            except (ValueError, AttributeError):
                # Если формат не ISO, пробуем YYYY-MM-DD
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Не удалось распарсить дату рецепта: {expiry_date_str}")
                    continue
            
            days_left = (expiry_date - today).days
            
            if days_left == 30:
                message = (
                    f"{EMOJI_REMINDER_PRESCRIPTION} Через месяц заканчивается рецепт на <b>{med['name']}</b>.\n"
                    f"Свяжись с врачом и получи новый рецепт."
                )
                
                for tg_user_id in users:
                    try:
                        await bot.send_message(tg_user_id, message)
                        logger.info(f"Отправлено напоминание о рецепте для {med['name']} пользователю {tg_user_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке напоминания пользователю {tg_user_id}: {e}")
    
    except Exception as e:
        logger.error(f"Ошибка при проверке рецептов: {e}")


async def check_stock(bot: Bot):
    """Проверяет остатки лекарств и отправляет напоминания за notify_before_days дней до окончания."""
    try:
        # Сначала уменьшаем остатки на daily_dose
        meds_service.decrease_daily_stock()
        
        medicines = meds_service.get_all_medicines()
        users = meds_service.get_all_users()
        
        if not users:
            logger.info("Нет зарегистрированных пользователей для отправки напоминаний")
            return
        
        for med in medicines:
            medicine_id = med["id"]
            name = med["name"]
            daily_dose = med["daily_dose"]
            current_stock = med["current_stock"]
            notify_before_days = med["notify_before_days"]
            
            if daily_dose <= 0:
                continue
            
            # Рассчитываем дни до окончания
            days_left = int(current_stock / daily_dose) if current_stock > 0 else 0
            
            # Проверяем, нужно ли отправить напоминание
            message = None
            if days_left == notify_before_days:
                message = (
                    f"{EMOJI_REMINDER_MEDICINE} Через {notify_before_days} дней у мамы закончится <b>{name}</b>.\n"
                    f"Купи, пожалуйста, новые упаковки."
                )
            elif days_left == 5 and notify_before_days != 5:
                message = (
                    f"{EMOJI_REMINDER_MEDICINE} Осталось 5 дней до окончания <b>{name}</b>.\n"
                    f"Напоминаю купить новые упаковки."
                )
            elif days_left == 0:
                message = (
                    f"{EMOJI_REMINDER_MEDICINE} У мамы закончилось <b>{name}</b>!\n"
                    f"Срочно купи новые упаковки."
                )

            if message:
                for tg_user_id in users:
                    try:
                        await bot.send_message(tg_user_id, message)
                        logger.info(f"Отправлено напоминание об остатке для {name} пользователю {tg_user_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке напоминания пользователю {tg_user_id}: {e}")
    
    except Exception as e:
        logger.error(f"Ошибка при проверке остатков: {e}")


async def start_scheduler(bot: Bot):
    """Запускает планировщик задач."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Планировщик уже запущен")
        return
    
    scheduler = AsyncIOScheduler()
    
    # Ежедневная проверка в полночь (00:00)
    scheduler.add_job(
        check_prescriptions,
        trigger="cron",
        hour=0,
        minute=0,
        args=(bot,),
        id="check_prescriptions",
        replace_existing=True
    )
    
    scheduler.add_job(
        check_stock,
        trigger="cron",
        hour=0,
        minute=0,
        args=(bot,),
        id="check_stock",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Планировщик задач запущен (проверки в 00:00 ежедневно)")

