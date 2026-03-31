from datetime import datetime, timedelta, time
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from database.database import database
from datetime import timedelta, timezone
import logging
from apscheduler.triggers.interval import IntervalTrigger

def get_keyboard(task_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнено", callback_data=f"done_{task_id}")
    return kb.as_markup()

async def send_reminder(bot: Bot, user_id, tg_id, task):
    try:
        print('в send_reminder пришло')
        date = f"{task[2]:%d.%m.%Y}"
        td = task[3]
        hours = td.seconds // 3600
        minutes = (td.seconds // 60) % 60
        time_task = f"{hours:02}:{minutes:02}"
        text = f"⏰ Напоминание!\nЗадача: {task[1]}\nДата: {date}\nВремя: {time_task}"
        await bot.send_message(chat_id=int(tg_id), text=text, reply_markup=get_keyboard(task[0]))

    except Exception as e:
        logging.info(f"Ошибка отправки {user_id}: {e}")

# проверка на просроченную задачу
def check_overdue_tasks():
    now = datetime.now()
    current_date = now.date()
    current_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    users_data = database.get_all_user()
    for user_id, _ in users_data:
        tasks = database.get_all_tasks(user_id)
        for task in tasks:
            if task[5] is None and (task[2] < current_date or
                                    (task[2] == current_date and task[3] < current_time)):
                database.edit_is_status_task(task[0], 0)  # если время прошло и статус None, меняем статус на просроченно
            # сброс по понедельникам
            if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
                database.edit_is_send_notification_period(task[0], 0)

def add_overdue_checker(scheduler):
    scheduler.add_job(
        check_overdue_tasks,
        trigger=IntervalTrigger(seconds=60),
        id="check_overdue_tasks")

def schedule_single_task(scheduler: AsyncIOScheduler, bot: Bot, user_id, tg_id, task):
    if task[5] is not None: #если задача просроченная\выполненная
        print('task[5] is not None')
        return
    tz_id = database.output_settings(user_id)[2]
    tz = database.get_timezone(tz_id)
    user_timezone = timezone(timedelta(hours=int(tz))) #часовой пояс с настроек берем
    print(f'tz = {tz}')
    td = task[3]
    # total_seconds = td.total_seconds()
    # hours = int(total_seconds // 3600)
    # minutes = int((total_seconds % 3600) // 60)
    #task_datetime = datetime.combine(task[2], time(hour=hours, minute=minutes))
    task_datetime = datetime.combine(task[2], datetime.min.time()) + td
    now_with_tz = datetime.now(user_timezone) #текущая дата с нужным часовым поясом
    task_time_utc = task_datetime.replace(tzinfo=user_timezone).astimezone(timezone.utc)
    print('Перед ифами')
    #если напоминание есть
    if task[4] is not None:
        notification_count = database.get_notification(int(task[4]))
        # время уведомления для напоминаний до задачи
        reminder_time_until = task_time_utc - timedelta(minutes=int(notification_count))
        print(task)
        print(task_time_utc)
        print(timedelta(minutes=int(notification_count)))
        print(notification_count)
        # пропускаем если напоминание до задачи уже прошло
        now_utc = datetime.now(timezone.utc)
        if reminder_time_until <= now_utc:
            logging.info("Время напоминания уже прошло")
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=task_time_utc),
                args=[bot, user_id, tg_id, task],
                id=f"rem_exact_{task[0]}",
                replace_existing=True)
            return
        periods = database.output_period_task(task[0])
        if periods: #если есть период
            for period in periods:
                now = datetime.now()
                if now.weekday() == (period - 1): #если сейчас этот день недели
                    database.edit_is_send_notification_period(task[0], 1, period) #меняем статус отправки напоминания
                    day = database.get_weekday(period)
                    logging.info(f"Напоминание отмечено отправленным в {day}")
        print('Перед add_job')
        print(reminder_time_until)
        print("REMINDER:", reminder_time_until)
        print("NOW UTC:", datetime.now(timezone.utc))
        print("DELTA:", reminder_time_until - datetime.now(timezone.utc))
        job = scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=reminder_time_until),
            args=[bot, user_id, tg_id, task],
            id=f"rem_before_{task[0]}",
            replace_existing=True)
        print("JOB ADDED:", scheduler.get_jobs())
        print("ADDED JOB:", job.id)
        print("NEXT RUN:", job.trigger)
    #если напоминания до задачи нет
    if task_time_utc > now_with_tz:
        print('Перед add_job2')
        job = scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=task_time_utc),
            args=[bot, user_id, tg_id, task],
            id=f"rem_exact_{task[0]}",
            replace_existing=True)
        print("JOB ADDED:", scheduler.get_jobs())
        print("ADDED JOB:", job.id)
        print("NEXT RUN:", job.trigger)

def schedule_all_tasks(scheduler: AsyncIOScheduler, bot: Bot):
    users_data = database.get_all_user() #список всех юзеров
    #может понадобиться проверка на наличие задач
    print('зашла в schedule_all_tasks')
    for user_id, tg_id in users_data:
        tasks = database.get_all_tasks(user_id)
        for task in tasks:
            schedule_single_task(scheduler, bot, user_id, tg_id, task)

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")
    schedule_all_tasks(scheduler, bot)
    # проверка каждую минуту на просрочку
    add_overdue_checker(scheduler)
    if not scheduler.running:  # если не запущен
        scheduler.start()
    return scheduler