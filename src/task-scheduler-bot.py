import asyncio
import logging
from dotenv import load_dotenv
import os


from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from routers.add_task import add_task_router
from routers.delete_task import delete_task_router
from routers.output_task import output_task_router
from routers.edit_task import edit_task_router
from routers.clear_task import clear_task_router
from routers.settings import settings_router
from commands.command import commands_router, set_bot_commands

#сделать напоминания по времени
#подключить бд
#сделать статистику по выполненным задачам
#доделать изменение задач, я не понимаю как подключить старые кнопки как при добавлении
#в amvera не обновляется data при добавлении


#сделать кнопки выполнения задач
#сделать вывод задач сегодня\на неделю




load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage()) #хранит состояние пользователя(на каком шаге находится)

logging.basicConfig(level=logging.INFO) #уровень логирования

main_router = Router()
dp.include_router(main_router) #добавляет роутер в поле зрения(в диспетчер)
dp.include_router(add_task_router)
dp.include_router(delete_task_router)
dp.include_router(output_task_router)
dp.include_router(edit_task_router)
dp.include_router(clear_task_router)
dp.include_router(settings_router)
dp.include_router(commands_router)

#--ЗАПУСК БОТА--
async def main():
    await set_bot_commands(bot) #задает команды для бота
    await dp.start_polling(bot) #обращается к серверу тг и проверяет на новые сообщения

if __name__ == "__main__": #если запускается из этого файла, то работает, если импортируется, то нет
    asyncio.run(main()) #запуск асинхронности