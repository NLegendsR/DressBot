import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import BOT_TOKEN
from handlers.admin import admin_router
from handlers.users import users_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set.")

    bot = Bot(BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(users_router)

    logging.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
