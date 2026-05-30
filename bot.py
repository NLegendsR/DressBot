import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN
from handlers.admin import admin_router
from handlers.users import users_router


async def main():
    try:
        bot = Bot(BOT_TOKEN)
        dp = Dispatcher()
        print("Bot start")
        dp.include_router(admin_router)
        dp.include_router(users_router)
        await dp.start_polling(bot)
    except Exception as ex:
        print(f"There is an exception {ex}")

if __name__ =='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit") 