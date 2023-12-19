import asyncio
import logging

import aiohttp
from aiogram import types
from aiogram.utils.exceptions import (
    BotBlocked,
    RetryAfter,
    UserDeactivated,
    ChatNotFound,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards import *
from keyboards import keyboard_send_start
from t_commands.db import *
from t_commands.handlers.settings import OrderSettings
from t_commands.handlers.start import OrderStart
from t_commands.make_collage import send_collage_message, get_object_from_minio
from t_commands.ref_system import send_referal_message
from t_commands.RateLimitMiddleware import limiter

scheduler = AsyncIOScheduler()


async def send_request_message(
    message, target_image_links, last=False, bot: Bot = None
):
    media = types.MediaGroup()
    source_path_list = []
    try:
        chat_id = message.chat.id
    except:
        chat_id = message
    async with aiohttp.ClientSession() as session:
        for link in target_image_links:
            try:
                source_path_temp, source_path = await get_object_from_minio(
                    link, session
                )
                source_path_list.append(source_path)
                media.attach_photo(types.InputFile(source_path), "")
            except Exception as e:
                logging.error(
                    "Ошибка в send_request_message MINIO_CLIENT.get_object", e
                )
            finally:
                source_path_temp.close()
                await source_path_temp.release()
    try:
        async with limiter:
            await limiter.acquire(len(media.media) + 5)
            await bot.send_media_group(chat_id=chat_id, media=media)
    except (UserDeactivated, ChatNotFound, BotBlocked) as e:
        print(f"Пользователь c id: {chat_id} заблокировал бота")
    except RetryAfter as e:
        print(f"Пользователь c id: {chat_id} заблокировал бота")
        await asyncio.sleep(e.timeout + 1)
        await bot.send_media_group(chat_id=chat_id, media=media)
    try:
        if last:
            text = """Понравились аватарки? Закажи еще❗️

Также ты можешь поменять свою фотографию в /settings и попробовать снова 👇🏼
            """
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(chat_id=chat_id, text=text)
    except (UserDeactivated, ChatNotFound, BotBlocked) as e:
        print(f"Пользователь c id: {chat_id} заблокировал бота")
    except RetryAfter as e:
        logging.error(f"Ошибка RetryAfter {e.timeout}", e)
        await asyncio.sleep(e.timeout + 1)
        await bot.send_message(chat_id=chat_id, text=text)


async def send_request_ref_message(
    bot: Bot, chat_id, target_image_links, last=False
):

    media = types.MediaGroup()
    for link in target_image_links:
        media.attach_photo(types.InputFile(link[0]), "")
    try:
        async with limiter:
            await limiter.acquire(len(media.media) + 5)
            await bot.send_media_group(chat_id=chat_id, media=media)
    except RetryAfter as e:
        logging.error(f"Ошибка RetryAfter {e.timeout}", e)
        await asyncio.sleep(e.timeout + 1)
        await bot.send_media_group(chat_id=chat_id, media=media)
    except (UserDeactivated, ChatNotFound, BotBlocked) as e:
        print(f"Пользователь c id: {chat_id} заблокировал бота")
    try:
        if last:
            text = """Круто что ты поделился с другом, вот твои аватарки.

Также ты можешь поменять свою фотографию в /settings и попробовать снова 👇🏼
            """
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(chat_id=chat_id, text=text)
    except RetryAfter as e:
        logging.error(f"Ошибка RetryAfter {e.timeout}", e)
        await asyncio.sleep(e.timeout + 1)
        await bot.send_message(chat_id=chat_id, text=text)
    except BotBlocked:
        print(f"Пользователь c id: {chat_id} заблокировал бота")


async def check_user_image_queue(dp: Dispatcher):
    """Проверяет в базе наличие выполненных задач в check_user_image_queue."""

    bot: Bot = dp.bot
    ready = await select_ready_in_check_user_image_queue()
    if not ready:
        return
    if (
        ready["request_type"] == USER_IMAGE_CHECK
        or ready["request_type"] == USER_IMAGES_CHECK_PACK
    ):
        print('здесь')
        if ready["check_analyse_face"] == 1:
            await set_user_image_links(
                ready["user_id"], ready["user_image_link"], 1
            )
            text = f"Принято всего изображений: 1 👍"
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(ready["user_id"], text)
            text = "Чтобы продолжить нажмите кнопку ниже 👇🏼"
            await dp.current_state(
                chat=ready["user_id"], user=ready["user_id"]
            ).set_state(OrderStart.send_photo.state)
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(
                    ready["user_id"],
                    text,
                    reply_markup=keyboard_send_start,
                )
        else:
            await dp.current_state(
                chat=ready["user_id"], user=ready["user_id"]
            ).set_state(OrderStart.send_gender.state)
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(
                    ready["user_id"],
                    "Лицо на изображениях не распознано ☹️ Попробуйте загрузить другую фотографию.",
                )
    else:
        user = await con_get_user_information(int(ready["user_id"]))
        # инлайн кнопки в настройках
        keyboard_settings = InlineKeyboardMarkup()
        keyboard_settings.add(
            *[
                InlineKeyboardButton(
                    text="Изменить гендер", callback_data="change_gender"
                ),
                InlineKeyboardButton(
                    text="Загрузить новое фото",
                    callback_data="change_own_photo",
                ),
            ]
        )
        keyboard_settings.add(
            InlineKeyboardButton(
                text="Поделиться реф. ссылкой с другом",
                switch_inline_query=f"""
Ниже моя реферальная ссылка 😌

👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼
{env["BOT_NAME"]}?start={user["ref_code"]}
👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻
""",
            )
        )
        gender = "мужской 🚹" if user.get("gender") == "male" else "женский 🚺"
        if ready["check_analyse_face"] == 1:
            async with aiohttp.ClientSession() as session:
                try:
                    source_path_temp = await MINIO_CLIENT.get_object(
                        "shawa", ready["user_image_link"], session
                    )
                    source_path = await source_path_temp.read()
                    if await update_user_image_links(
                        ready["user_id"], ready["user_image_link"]
                    ):
                        text = f"Принято всего изображений: 1 👍"
                        async with limiter:
                            await limiter.acquire(8)
                            await bot.send_message(ready["user_id"], text)
                            await bot.send_photo(
                                chat_id=ready["user_id"],
                                photo=source_path,
                                caption=f"""Ваше текущее фото ☝️
                    
Ваш гендер: {gender}

Реферальная ссылка: {env["BOT_NAME"]}?start={user["ref_code"]}
                                """,
                                reply_markup=keyboard_settings,
                            )
                            await bot.send_message(
                                ready["user_id"],
                                "Фото успешно обновлено",
                                reply_markup=keyboard_back_to_tarif,
                            )
                        await dp.current_state(
                            chat=ready["user_id"], user=ready["user_id"]
                        ).set_state(OrderSettings.send_settings.state)
                except Exception as e:
                    logging.error(
                        "Ошибка в successful_payment MINIO_CLIENT.get_object",
                        e,
                    )
                finally:
                    source_path_temp.close()
                    await source_path_temp.release()
                    await session.close()
        else:
            async with limiter:
                await limiter.acquire(2)
                await bot.send_message(
                    ready["user_id"],
                    "Лицо на изображении не распознано ☹️ Попробуйте загрузить другую фотографию.",
                    reply_markup=keyboard_back_to_tarif,
                )
            await dp.current_state(
                chat=ready["user_id"], user=ready["user_id"]
            ).set_state(OrderSettings.send_settings.state)
    await check_user_image_queue(dp)


async def check_for_ready_queue(dp: Dispatcher):
    """Проверяет в базе наличие выполненных задач в user_images и queue."""

    bot = dp.bot
    ready = await select_ready_images()
    if not ready:
        return
    target_image_links = ready["image_target_link"].split(";;")
    if (
        
        ready["image_tarif"] == IMAGE_FOR_REFERAL
    ):
        await send_request_message(
            ready["user_id"], target_image_links, last=True, bot=bot
        )
        await send_referal_message(
            bot, ready["user_id"], ready["image_request_id"]
        )
    elif ready["image_tarif"] == IMAGE_PAID:
        for i, target_image_link in enumerate(target_image_links):
            if (i + 1) % 10 == 0 or (i + 1) == len(target_image_links):
                await send_request_message(
                    ready["user_id"],
                    target_image_links[i - 9 : i + 1],
                    last=True if len(target_image_links) == i + 1 else False,
                    bot=bot,
                )
        try:
            for i in target_image_links:
                await MINIO_CLIENT.remove_object("shawa", i)
        except Exception as e:
            logging.error(
                "Ошибка в check_for_ready_queue MINIO_CLIENT.get_object",
                e,
            )
    if (
        ready["image_tarif"] == IMAGE_COLLAGE_50
       
    ):
        collage_link = await con_get_collage_link(ready["image_request_id"])
        if collage_link:
            await change_collage_status_sent(ready["image_request_id"])
        await send_collage_message(
            ready["user_id"],
            collage_link["image_collage_link"],
            ready["image_request_number"],
        )
    await check_for_ready_queue(dp)
    return True
