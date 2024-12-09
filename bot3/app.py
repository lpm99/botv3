import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from middlewares.db import DataBaseSession

from database.engine import create_db, session_maker

from handlers import user_private, admin_private_category
from handlers.user_group import user_group_router
from handlers.admin_private import admin_router
from config import TELEGRAM_BOT_TOKEN


logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
bot.my_admins_list = []

dp = Dispatcher()

dp.include_router(user_private.router)
dp.include_router(user_group_router)
dp.include_router(admin_router)
dp.include_router(admin_private_category.router)


async def on_startup(bot):

    await create_db()


async def main():
    dp.startup.register(on_startup)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
