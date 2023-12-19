import os
from distutils.util import strtobool
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio


from t_commands.RateLimitMiddleware import RateLimitMiddleware
from typing import Any, Awaitable, Callable, Dict
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.types.base import TelegramObject
from aiogram.types import Message





class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, storage: RedisStorage):
        super().__init__()
        self.storage = storage

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], 
                       event: Message, data: Dict[str, Any]) -> Any:
        user = f'user{event.from_user.id}'
        
        check_user = await self.storage.redis.get(name=user)
        
        if check_user:
            if int(check_user.decode()) == 1:
                # Удаляем предыдущие сообщения пользователя
                await self.delete_previous_messages(event.chat.id, event.from_user.id)
                return await event.answer('Слишком быстро..Ждите 10 секунд')

        await self.storage.redis.set(name=user, value=1, ex=10)
        return await handler(event, data)

    async def delete_previous_messages(self, chat_id, user_id):
        try:
            messages = await bot.get_chat_history(chat_id, limit=10)
            for message in messages:
                if message.from_user.id == user_id:
                    await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete previous messages: {e}")





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

bot = Bot(token=env["TG_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(
    env["REDIS_HOST"],
    int(env["REDIS_PORT"]),
    db=int(env["REDIS_DATABASE"]),
    pool_size=int(env["REDIS_POOL_SIZE"]),
)
dp = Dispatcher(bot, storage=storage)


dp.middleware.setup(ThrottlingMiddleware(storage=storage))

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
