import asyncio
import concurrent.futures
import io
import logging
import random
from aiogram import Bot

import aiohttp
from aiogram.utils.exceptions import BotBlocked

from constants import *
from t_commands.db import *
from t_commands.handlers.select_tarif import get_user_references_remaining


async def send_referal_message(bot: Bot, message_from_id, user_images_id):
    try:
        user = await con_get_user_information(message_from_id)
        if not user:
            await bot.send_message(
                chat_id=message_from_id,
                text="""Пользователь не найден.☹️
            
Пожалуйста пройдите авторизацию, нажав команду /start
            """,
            )
            return
        ref_collage_link = await con_get_collage_link(user_images_id)
        if ref_collage_link:
            ref_collage_link = ref_collage_link["image_collage_link"]
            await change_collage_status_sent(user_images_id)
        caption = f"""Как тебе аватарки 👆🏼 ❓ 

Хочешь такие же  ❓

Вот ссылка: {env["BOT_NAME"]}?start={user[11]}
        """
        async with aiohttp.ClientSession() as session:
            try:
                source_path_temp = await MINIO_CLIENT.get_object(
                    "shawa", ref_collage_link, session
                )
                source_path = io.BytesIO(await source_path_temp.read())
                await bot.send_photo(
                    chat_id=message_from_id,
                    photo=source_path,
                    caption=caption,
                )
            except BotBlocked:
                print(
                    f"Пользователь c id: {message_from_id} заблокировал бота"
                )
                return
            except Exception as e:
                logging.error(
                    "Ошибка в send_referal_message MINIO_CLIENT.get_object", e
                )
            finally:
                source_path_temp.close()
                await source_path_temp.release()
                await session.close()
        await asyncio.sleep(1)
        await bot.send_message(
            chat_id=message_from_id,
            text="""Отправь другу сообщение выше ☝️

И получи 5 аватарок в подарок 💝 если друг зарегистрируется по твоей ссылке.
            """,
        )
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, file_remove, *(ref_collage_link,))
        return ref_collage_link
    except BotBlocked:
        print(f"Пользователь c id: {message_from_id} заблокировал бота")
        return


async def send_ready_referal_message(message_from_id, user_images_id, db):
    try:
        user = await get_user_information(message_from_id, db)
        if not user:
            await bot.send_message(
                chat_id=message_from_id,
                text="""Пользователь не найден.☹️
            
Пожалуйста пройдите авторизацию, нажав команду /start
            """,
            )
            return
        caption = f"""Как тебе аватарки 👆🏼 ❓ 

Хочешь такие же  ❓

Вот ссылка: {env["BOT_NAME"]}?start={user[11]}
        """

        ref_collage_link = await get_collage_link(user_images_id, db)
        ref_collage_link = ref_collage_link["image_collage_link"]
        async with aiohttp.ClientSession() as session:
            try:
                source_path_temp = await MINIO_CLIENT.get_object(
                    "shawa", ref_collage_link, session
                )
                source_path = await source_path_temp.read()
                await bot.send_photo(
                    chat_id=message_from_id,
                    photo=source_path,
                    caption=caption,
                )
            except Exception as e:
                logging.error(
                    "Ошибка в make_ref_collage MINIO_CLIENT.get_object",
                    e,
                )
            finally:
                source_path_temp.close()
                await source_path_temp.release()
                await session.close()
        await asyncio.sleep(1)
        await bot.send_message(
            chat_id=message_from_id,
            text="""Отправь другу сообщение выше ☝️

И получи 5 аватарок в подарок 💝 если друг зарегистрируется по твоей ссылке.
            """,
        )
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, file_remove, *(ref_collage_link,))

        return ref_collage_link
    except BotBlocked:
        print(f"Пользователь c id: {message_from_id} заблокировал бота")


async def add_to_queue_ref(user_id, request_type, count_photo, db):
    """Функция добавляет задачи на генерацию фото в очередь."""

    id_in_user_images = await add_pending_image_request(
        user_id, request_type, db
    )
    if not id_in_user_images:
        return
    id_in_history_collage_links = None
    (
        user_references,
        current_user_image_link,
    ) = await get_user_references_remaining(user_id, db)
    if len(user_references) >= count_photo:
        keys_choice = random.sample(list(user_references), k=count_photo)
        image_reference_link_list = []
        for n, item in enumerate(keys_choice):
            image_reference_link_list.append(
                random.choices(user_references.get(item))[0]
            )
        image_reference_links = ";;".join(image_reference_link_list)
        await add_user_image_request_to_queue(
            user_id,
            n + 1,
            id_in_user_images,
            image_reference_links,
            current_user_image_link,
            count_photo,
            request_type,
            db,
            id_in_history_collage_links,
        )
