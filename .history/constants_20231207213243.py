import os
from distutils.util import strtobool
from pathlib import Path
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio
from aiogram.types.base import TelegramObject

from typing import Union

from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

# from minio import Minio


dotenv_path = Path(".env.dev")
load_dotenv(dotenv_path=dotenv_path)    
env = os.environ


SEND_TARIF_TURBO = "То что вам нужно 10: 10$"

SEND_SELECT_TARIF = "Выбрать тариф"
SEND_SELECT_OTHER_TARIF = "Выбрать другой тариф"
SEND_BACK_TO_TARIF = "Вернуться обратно"
SETTINGS = "Настройки"
GET_FREE_AVATARS = "Получить аватарки"
AVA_50 = "50 аватарок"

USER_IMAGE_CHECK = "image_check"
USER_IMAGES_CHECK_PACK = "images_check_pack"
USER_IMAGE_CHECK_LK = "image_check_lk"
USER_IMAGES_CHECK_PACK_LK = "images_check_pack_lk"
IMAGE_FREE = "image_free"
IMAGE_FOR_REFERAL = "image_for_referal"
IMAGE_PAID = "image_paid"
TARIF_TURBO = "tarif-turbo"
TARIF_PREMIUM = "tarif-premium"

IMAGE_COLLAGE_50 = "image_collage_50"

COUNT_PHOTO_FREE = 5
COUNT_PHOTO_TURBO = 10
COUNT_PHOTO_PREM = 100
COUNT_PHOTO_FOR_REFERAL = 5
REQUEST_TO_QUEUE_INTERVAL = 1
REQUEST_TO_QUEUE_FOR_READY_INTERVAL = 5
TURBO_RUB = 20000
PREMIUM_RUB = 30000
PENDING = "pending"  # в ожидании обработки в очереди
DRAWING = "drawing"  # взято в работу нейросетью
READY = "ready"  # нейронка выполнила работу, необходимо отправить пользователю
SENT = "sent"  # отправлено пользователю
BUCKET_NAME = "shawa"

TRUE_AGE = "Мне есть 18 лет!"

FALSE_AGE = "Мне нет 18 лет!"


DATETIME_FORMAT = "%d.%m.%Y_%H:%M:%S"


loop = asyncio.get_event_loop()


bot = Bot(token=env["TG_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(
    env["REDIS_HOST"],
    int(env["REDIS_PORT"]),
    db=int(env["REDIS_DATABASE"]),
    pool_size=int(env["REDIS_POOL_SIZE"]),
)









def rate_limit(limit: int, key=None):
    """
    Decorator for configuring rate limit and key in different functions.
    :param limit:
    :param key:
    :return:
    """

    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple middleware
    """

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        """
        This handler is called when dispatcher receives a message
        :param message:
        """
        # Get current handler
        handler = current_handler.get()

        # Get dispatcher from context
        dispatcher = Dispatcher.get_current()
        # If handler was configured, get rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Execute action
            await self.message_throttled(message, t)

            # Cancel current handler
            raise CancelHandler()
    
    async def on_process_callback_query(self, query: types.CallbackQuery, data: dict):
        # Get current handler
        handler = current_handler.get()

        # Get dispatcher from context
        dispatcher = Dispatcher.get_current()
        # If handler was configured, get rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Execute action
            await self.callback_query_throttled(query, t)

            # Cancel current handler
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        """
        Notify user only on first exceed and notify about unlocking only on last exceed
        :param message:
        :param throttled:
        """
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply('Too many requests! ')

        # Sleep.
        await asyncio.sleep(delta)

        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await message.reply('Unlocked.')

    async def callback_query_throttled(self, query: types.CallbackQuery, throttled: Throttled):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await query.answer('Too many requests! ', show_alert=True)




dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(ThrottlingMiddleware())

MINIO_CLIENT = Minio(
    env["MINIO_SERVER"],
    access_key=env["MINIO_ROOT_USER"],
    secret_key=env["MINIO_ROOT_PASSWORD"],
    secure=strtobool(env["MINIO_SECURE"]),
)


def file_remove(new_file_path, image_jpg=None):
    if os.path.isfile(new_file_path):
        if image_jpg:
            image_jpg.close()
        os.remove(new_file_path)