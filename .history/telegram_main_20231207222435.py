import asyncio
import logging

from aiogram.types import BotCommand
from aiogram import executor
from bot_sheduler import *
from constants import bot, dp
from db.db import DatabaseMiddleware
from keyboards import *
from t_commands.AlbumMiddleware import AlbumMiddleware
from t_commands.create_table import create_table
from t_commands.handlers.help import register_send_help
from t_commands.handlers.select_tarif import register_select_tarif
from t_commands.handlers.settings import register_settings
from t_commands.handlers.start import register_handler_start
from t_commands.RateLimitMiddleware import RateLimitMiddleware




logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.getLogger("apscheduler.executors.default").setLevel(logging.ERROR)
logging.getLogger("apscheduler.scheduler").setLevel(logging.ERROR)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запуск бота"),
        BotCommand(
            command="/settings", description="Настройки (замена фото, пола)"
        ),
        BotCommand(command="/help", description="Как использовать бота"),
    ]
    await bot.set_my_commands(commands)


async def start_scheduler(dp):
    logging.info("Shedule starting...")
    scheduler.add_job(
        check_for_ready_queue,
        trigger="interval",
        seconds=REQUEST_TO_QUEUE_FOR_READY_INTERVAL,
        args=[
            dp,
        ],
    )
    scheduler.add_job(
        check_user_image_queue,
        trigger="interval",
        seconds=REQUEST_TO_QUEUE_INTERVAL,
        args=[
            dp,
        ],
    )
    scheduler.start()
    # await asyncio.Event().wait()


async def start_bot(dp):
    logging.info("Starting bot")
    await dp.start_polling()


async def main():
    await create_table()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(message)s",
    )

    register_handler_start(dp)
    register_select_tarif(dp)
    register_settings(dp)
    register_send_help(dp)

    await set_commands(bot)

    await dp.skip_updates()
    dp.middleware.setup(DatabaseMiddleware())
    dp.middleware.setup(AlbumMiddleware())
    dp.middleware.setup(RateLimitMiddleware())

    await start_scheduler(dp)

    await start_bot(dp)
    # await asyncio.gather(start_scheduler(), start_bot())


if __name__ == "__main__":
    asyncio.run(main())
