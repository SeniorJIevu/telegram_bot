import os
from distutils.util import strtobool
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from dotenv import load_dotenv
from miniopy_async import Minio


from aiogram.types import CallbackQuery
from t_commands.RateLimitMiddleware import RateLimitMiddleware
from typing import Any, Awaitable, Callable, Dict
from aiogram.dispatcher.middlewares import BaseMiddleware, AbortMiddleware
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.types.base import TelegramObject
from aiogram.types import Message
import time


class DeletePreviousMessageMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: Message, data: dict):
        # Удаляем предыдущее сообщение, если оно есть
        if message.reply_to_message:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            except Exception as e:
                print(f"Failed to delete previous message: {e}")

    async def on_pre_process_callback_query(self, callback_query: CallbackQuery, data: dict):
        # Удаляем предыдущее сообщение, если оно есть
        if callback_query.message.reply_to_message:
            try:
                await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.reply_to_message.message_id)
            except Exception as e:
                print(f"Failed to delete previous message: {e}")

    async def on_post_process_message(self, message: Message, result, data: dict):
        # Удаляем текущее сообщение после обработки
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            print(f"Failed to delete current message: {e}")

        # Здесь можно добавить логику после обработки нового сообщения

    async def on_post_process_callback_query(self, callback_query: CallbackQuery, result, data: dict):
        # Удаляем текущее сообщение после обработки
        try:
            await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            print(f"Failed to delete current message: {e}")


class InlineButtonClickThrottleMiddleware(BaseMiddleware):
    def __init__(self, cooldown_time: int = 10):
        self.cooldown_time = cooldown_time
        self.last_click_times = {}

    async def on_pre_process_callback_query(self, callback_query: CallbackQuery, data: dict):
        # Проверяем, есть ли у пользователя время последнего нажатия
        user_id = callback_query.from_user.id
        last_click_time = self.last_click_times.get(user_id, 0)

        # Проверяем, прошло ли достаточно времени с последнего нажатия
        current_time = time.time()
        if current_time - last_click_time < self.cooldown_time:
            await callback_query.answer("Пожалуйста, подождите немного перед повторным нажатием.")
            # Блокируем обработку запроса
            raise AbortMiddleware()

        # Обновляем время последнего нажатия пользователя
        self.last_click_times[user_id] = current_time

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


dp.middleware.setup(DeletePreviousMessageMiddleware())
dp.middleware.setup(InlineButtonClickThrottleMiddleware())
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
