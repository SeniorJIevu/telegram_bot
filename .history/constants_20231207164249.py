import os
from distutils.util import strtobool
from pathlib import Path
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio
from aiogram.types.base import TelegramObject


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

bot = Bot(token=env["TG_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(
    env["REDIS_HOST"],
    int(env["REDIS_PORT"]),
    db=int(env["REDIS_DATABASE"]),
    pool_size=int(env["REDIS_POOL_SIZE"]),
)



def rate_limit():
     return 5  > 2


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: callable[[TelegramObject, dict[str, Any], Awaitable[Any]]],
        event: TelegramObject, 
        data: Dict:[str, Any],
        
    )










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
