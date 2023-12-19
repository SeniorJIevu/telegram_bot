import os
from distutils.util import strtobool
from pathlib import Path
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio


# from minio import Minio
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Awaitable,Callable
dotenv_path = Path(".env.dev")
load_dotenv(dotenv_path=dotenv_path)

env = os.environ


SEND_TARIF_TURBO = "Супер 50: 200 RUB ⚡️"

SEND_SELECT_TARIF = "Выбрать тариф"
SEND_SELECT_OTHER_TARIF = "Выбрать другой тариф"
SEND_BACK_TO_TARIF = "Вернуться обратно"
SETTINGS = "Настройки"
GET_FREE_AVATARS = "Получить аватарки"
AVA_50 = "10 аватарок"

USER_IMAGE_CHECK = "image_check"
USER_IMAGES_CHECK_PACK = "images_check_pack"
USER_IMAGE_CHECK_LK = "image_check_lk"
USER_IMAGES_CHECK_PACK_LK = "images_check_pack_lk"

IMAGE_FOR_REFERAL = "image_for_referal"
IMAGE_PAID = "image_paid"
TARIF_TURBO = "tarif-turbo"


IMAGE_COLLAGE_50 = "image_collage_50"


COUNT_PHOTO_TURBO = 10

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


from aiogram.dispatcher.filters import BoundFilter

class NoSpamFilter(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        # Проверяем, является ли сообщение типом текстового сообщения
        if isinstance(message, types.Message):
            # Проверяем, что текст сообщения не пустой
            if message.text:
                # Получаем последние 5 сообщений из чата
                messages = await message.bot.get_chat_history(chat_id=message.chat.id, limit=2)
                # Проверяем, есть ли среди них такие же сообщения как текущее
                if any(m.text == message.text for m in messages):
                    return False  # Возвращаем False, если найдено повторяющееся сообщение
        return True  # Возвращаем True, если сообщение прошло фильтр

class NoButtonSpamFilter(BoundFilter):
    async def __call__(self, query: types.CallbackQuery) -> bool:
        # Проверяем, было ли уже нажатие на данную inline кнопку
        if query.data in query.message.reply_markup.inline_keyboard:
            await query.answer('Кнопка')
            return False  # Возвращаем False, если кнопка уже была нажата
        return True  # Возвращаем True, если запрос прошел фильтр




bot = Bot(token=env["TG_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(
    env["REDIS_HOST"],
    int(env["REDIS_PORT"]),
    db=int(env["REDIS_DATABASE"]),
    pool_size=int(env["REDIS_POOL_SIZE"]),
)
dp = Dispatcher(bot, storage=storage)
dp.filters_factory.bind(NoSpamFilter)
dp.filters_factory.bind(NoButtonSpamFilter)




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
