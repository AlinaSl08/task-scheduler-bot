import datetime
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from commands.command import DATA_FILE_PATH
from database.db import read_from_file


def get_keyboard(task_id: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Выполнено", callback_data=f"done_{task_id}")
    return kb.as_markup()


async def send_reminder(bot: Bot, user_id: str, task: dict):
    text = f"⏰ Напоминание!\nЗадача: {task['name']}\nВремя: {task['time']['hour']}:{task['time']['minute']}"
    try:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=get_keyboard(task.get('id', 'no_id')))
    except Exception as e:
        print(f"Ошибка отправки {user_id}: {e}")



def schedule_single_task(scheduler: AsyncIOScheduler, bot: Bot, user_id: str, task: dict):
    if task.get('completed') or task['notification'] == "Без напоминаний":
        return
    task_date = task['date']
    task_time = datetime.datetime(
            year=int(task_date['year']),
            month=int(task_date['month']),
            day=int(task_date['day']),
            hour=int(task['time']['hour']),
            minute=int(task['time']['minute']),
            second=0,
            microsecond=0,
            tzinfo=datetime.timezone.utc)

    # Время уведомления
    reminder_time = task_time - datetime.timedelta(minutes=int(task['notification']))
    # Пропускаем если напоминание уже прошло
    if reminder_time <= datetime.datetime.now(datetime.timezone.utc):
        print("Время напоминания уже прошло")
    print("Сюда пришло")
    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=reminder_time),
        kwargs={"bot": bot, "user_id": user_id, "task": task}
    )


def schedule_all_tasks(scheduler: AsyncIOScheduler, bot: Bot):
    users_data = {}
    read_from_file(DATA_FILE_PATH, users_data)

    for user_id, tasks in users_data.items():
        for task in tasks:
            schedule_single_task(scheduler, bot, user_id, task)


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")

    schedule_all_tasks(scheduler, bot)
    if not scheduler.running:  # предотвращаем "Scheduler is already running"
        scheduler.start()
    return scheduler