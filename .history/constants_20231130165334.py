import os
from distutils.util import strtobool
from pathlib import Path

from aiogram import Bot, Dispatcher, types, ctx
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio
import math
import asyncio
from aiogram.types import CallbackQuery
from t_commands.RateLimitMiddleware import RateLimitMiddleware
from typing import Any, Awaitable, Callable, Dict
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler, ctx_data
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
import time
import time
import asyncio
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled, MessageCantBeDeleted
from aiogram.utils import context


admins = 'creator', 'administrator'

class CallbackAntiFlood(BaseMiddleware):

    def __init__(self):
        super(CallbackAntiFlood, self).__init__()

    @staticmethod
    async def on_pre_process_callback_query(call: types.CallbackQuery):
        """
        Этот обработчик вызывается, когда диспетчер получает обновление о нажатии кнопки
        """
        if call.message:
            if call.message.from_user:
                # Получить диспетчер из контекста
                Dispatcher.get_current()

                # Использовать Dispatcher.throttle метод
                try:
                    await dispatcher.throttle('settings_callback', rate=0.5)
                except Throttled as throttled:
                    response = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
                    if response.status not in admins:
                        
                        # Заблокировать
                        if throttled.exceeded_count <= 2:
                            name = call.from_user.full_name
                            user_id = call.from_user.id
                            await bot.kick_chat_member(call.message.chat.id, user_id,
                                                       until_date=math.floor(time.time()) + 10 * 60)
                            await bot.send_message(call.message.chat.id,
                                                   f'[{name}](tg://user?id={user_id}) заблокирован '
                                                   'на 10 минут за бездумное нажатие по кнопкам :).')
                        # Отменить текущий обработчик
                        raise CancelHandler()  












####################################################


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
            await message.answer('Слишком много идентичных запросов, ждите ! :) ')

        # Sleep.
        await asyncio.sleep(delta)

        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await message.answer('Вы снова можете писать :)')



# from minio import Minio

dotenv_path = Path(".env.dev")
load_dotenv(dotenv_path=dotenv_path)

env = os.environ

SEND_TARIF_FREE = "Бесплатно"
SEND_TARIF_TURBO = "Супер 50: 200 RUB ⚡️"
SEND_TARIF_PREMIUM = "Премиум 100: 300 RUB"
SEND_SELECT_TARIF = "Выбрать тариф"
SEND_SELECT_OTHER_TARIF = "Выбрать другой тариф"
SEND_BACK_TO_TARIF = "Вернуться обратно"
SETTINGS = "Настройки"
GET_FREE_AVATARS = "Получить аватарки"
AVA_50 = "50 аватарок"
AVA_100 = "100 аватарок"
USER_IMAGE_CHECK = "image_check"
USER_IMAGES_CHECK_PACK = "images_check_pack"
USER_IMAGE_CHECK_LK = "image_check_lk"
USER_IMAGES_CHECK_PACK_LK = "images_check_pack_lk"
IMAGE_FREE = "image_free"
IMAGE_FOR_REFERAL = "image_for_referal"
IMAGE_PAID = "image_paid"
TARIF_TURBO = "tarif-turbo"
TARIF_PREMIUM = "tarif-premium"
IMAGE_COLLAGE_5 = "image_collage_5"
IMAGE_COLLAGE_50 = "image_collage_50"
IMAGE_COLLAGE_100 = "image_collage_100"
COUNT_PHOTO_FREE = 5
COUNT_PHOTO_TURBO = 50
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

DATETIME_FORMAT = "%d.%m.%Y_%H:%M:%S"


class ButtonRateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.last_button_ids = {}

    async def on_process_callback_query(self, query: types.CallbackQuery, data: dict):
        button_id = query.data
        current_time = time.time()

        if button_id in self.last_button_ids and current_time - self.last_button_ids[button_id] < 10:
            await query.answer("Please wait for 10 seconds before pressing the same button again.")
            return False
        else:
            self.last_button_ids[button_id] = current_time
            await self.update_last_button_id(button_id, current_time)
            return True

    async def update_last_button_id(self, button_id, current_time):
        self.last_button_ids[button_id] = current_time




bot = Bot(token=env["TG_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(
    env["REDIS_HOST"],
    int(env["REDIS_PORT"]),
    db=int(env["REDIS_DATABASE"]),
    pool_size=int(env["REDIS_POOL_SIZE"]),
)

dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(ThrottlingMiddleware())
dp.middleware.setup(CallbackAntiFlood())


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