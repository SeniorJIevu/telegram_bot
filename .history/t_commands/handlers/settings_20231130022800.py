import io
import logging
import uuid
from typing import List

import aiohttp
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from constants import env
from keyboards import *
from t_commands.db import *
from t_commands.handlers.select_tarif import TarifStart, send_select_tarif
from t_commands.handlers.start import prevent_double_click

class OrderSettings(StatesGroup):
    send_settings = State()

@dp.callback_query_handler(lambda el: el.data == 'change_own_photo',state=OrderSettings.send_settings)
@prevent_double_click
async def change_own_photo(call: types.CallbackQuery, db: asyncpg.pool.Pool):
    await call.message.answer(
        "Загрузите новую фотографию 👇🏼",
        reply_markup=keyboard_back_to_tarif,
    )


async def send_settings_photo_group(
    message: types.Message,
    album: List[types.Message],
    state: FSMContext,
    db: asyncpg.pool.Pool,
):
    if message.content_type == "text" and message.text != "SEND_BACK_TO_TARIF":
        await message.answer(
            "Для смены фотографии отправьте данные в виде изображения!",
            reply_markup=keyboard_back_to_tarif,
        )
        return
    if message.content_type != "photo":
        await message.answer(
            "Для смены фотографии отправьте данные в виде изображения!",
            reply_markup=keyboard_back_to_tarif,
        )
        return
    user = await get_user_information(message.from_id, db)
    if not user:
        await message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return

    gender = "мужской 🚹" if user.get("gender") == "male" else "женский 🚺"
    last_msg = await message.answer("Обрабатываем изображение... ⏳")

    image_path_list = []
    for id, message_photo in enumerate(album):
        if message_photo.content_type != "photo":
            continue
        photo = io.BytesIO()
        await message_photo.photo[-1].download(destination_file=photo)
        photo.seek(0)
        new_file_path = (
            f"images/{message.from_id}/photos/{uuid.uuid4().hex}.jpg"
        )
        try:
            await MINIO_CLIENT.put_object(
                "shawa", new_file_path, photo, len(photo.getvalue())
            )
        except Exception as e:
            logging.error(
                "Ошибка в send_settings_photo_group MINIO_CLIENT.get_object",
                e,
            )
        image_path_list.append(new_file_path)
    image_path_str = ";;".join(image_path_list)
    await add_to_check_user_image_queue(
        message, USER_IMAGES_CHECK_PACK_LK, image_path_str, db
    )


async def send_settings_photo(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    if message.content_type == "text" and message.text != "SEND_BACK_TO_TARIF":
        await message.answer(
            "Для смены фотографии отправьте данные в виде изображения!",
            reply_markup=keyboard_back_to_tarif,
        )
        return

    if message.content_type != "photo":
        await message.answer(
            "Для смены фотографии отправьте данные в виде изображения!",
            reply_markup=keyboard_back_to_tarif,
        )
        return

    user = await get_user_information(message.from_id, db)
    if not user:
        await message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    gender = "мужской 🚹" if user.get("gender") == "male" else "женский 🚺"
    last_msg = await message.answer("Обрабатываем изображение... ⏳")
    photo = io.BytesIO()
    await message.photo[-1].download(destination_file=photo)
    photo.seek(0)
    new_file_path = f"images/{message.from_id}/photos/{uuid.uuid4().hex}.jpg"
    try:
        await MINIO_CLIENT.put_object(
            "shawa", new_file_path, photo, len(photo.getvalue())
        )
    except Exception as e:
        logging.error(
            "Ошибка в send_settings_photo MINIO_CLIENT.fput_object",
            e,
        )
    await add_to_check_user_image_queue(
        message, USER_IMAGE_CHECK_LK, new_file_path, db
    )

@dp.callback_query_handler(lambda el: el.data == 'change_gender', state=OrderSettings.send_settings)
@prevent_double_click
async def change_gender(call: types.CallbackQuery, db: asyncpg.pool.Pool):
    user = await get_user_information(call.from_user.id, db)
    if not user:
        await call.message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    # инлайн кнопки в настройках
    keyboard_settings = InlineKeyboardMarkup()
    keyboard_settings.add(
        *[
            InlineKeyboardButton(
                text="Изменить гендер", callback_data="change_gender"
            ),
            InlineKeyboardButton(
                text="Загрузить новое фото", callback_data="change_own_photo"
            ),
        ]
    )
    keyboard_settings.add(
        InlineKeyboardButton(
            text="Поделиться реф. ссылкой с другом",
            switch_inline_query=f"""
Ниже моя реферальная ссылка 😌

👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼 👇🏼
{env["BOT_NAME"]}?start={user["ref_code"]}
👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻 👆🏻
""",
        )
    )
    gender = "female" if user.get("gender") == "male" else "male"
    await user_update_gender(call.from_user.id, gender, db)
    gender = "мужской 🚹" if gender == "male" else "женский 🚺"
    async with aiohttp.ClientSession() as session:
        try:
            source_path_temp = await MINIO_CLIENT.get_object(
                "shawa", user.get("image_link"), session
            )
            source_path = await source_path_temp.read()
            await call.message.delete()
            await call.message.answer_photo(
                photo=source_path,
                caption=f"""Ваше текущее фото ☝️
            
Ваш гендер: {gender}

Реферальная ссылка: {env["BOT_NAME"]}?start={user["ref_code"]}
            """,
                reply_markup=keyboard_settings,
            )
        except Exception as e:
            logging.error(
                "Ошибка в send_settings_photo MINIO_CLIENT.get_object", e
            )
        finally:
            source_path_temp.close()
            await source_path_temp.release()
            await session.close()
    await call.message.answer(
        "Гендер изменен",
        reply_markup=keyboard_back_to_tarif,
    )

@dp.message_handler(state=TarifStart.send_settings_rarif)
async def settings(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    print('Настроечки')
    user = await get_user_information(message.chat.id, db)
    if not user:
        await message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    # инлайн кнопки в настройках
    keyboard_settings = InlineKeyboardMarkup()
    keyboard_settings.add(
        *[
            InlineKeyboardButton(
                text="Изменить гендер", callback_data="change_gender"
            ),
            InlineKeyboardButton(
                text="Загрузить новое фото", callback_data="change_own_photo"
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
    async with aiohttp.ClientSession() as session:
        photo = io.BytesIO()
        try:
            photo = await MINIO_CLIENT.get_object(
                "shawa", user.get("image_link"), session
            )
            source_path = await photo.read()
            await message.answer_photo(
                photo=source_path,
                caption=f"""Ваше текущее фото ☝️
                
Ваш гендер: {gender}

Реферальная ссылка: {env["BOT_NAME"]}?start={user["ref_code"]}
                """,
                reply_markup=keyboard_settings,
            )
        except Exception as e:
            await message.answer(
                text=f"""Фото не найдено
                
Ваш гендер: {gender}

Реферальная ссылка: {env["BOT_NAME"]}?start={user["ref_code"]}
                """,
                reply_markup=keyboard_settings,
            )
            logging.error("Ошибка в settings MINIO_CLIENT.get_object", e)
        finally:
            photo.close()
            await session.close()
    await message.answer(
        "Вы можете заменить Вашу текущую фотографию на новую, изменить пол, либо поделиться реферальной ссылкой с другом и получить 5 аватарок бесплатно 😌",
        reply_markup=keyboard_back_to_tarif,
    )
    await state.set_state(OrderSettings.send_settings.state)

@dp.callback_query_handler(state=(TarifStart.send_select_tarif.state, OrderSettings.send_settings))
@prevent_double_click
async def back_to_tarif(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    await state.set_state(TarifStart.send_select_tarif.state)
    await send_select_tarif(call, state, db)


def register_settings(dp: Dispatcher):
    dp.register_message_handler(
        settings,
        commands="settings",
        state="*",
    )
    dp.register_callback_query_handler(
        settings,
        text=SETTINGS,
        state=TarifStart.send_settings_rarif,
    )
    dp.register_message_handler(
        back_to_tarif,
        Text(equals=SEND_BACK_TO_TARIF, ignore_case=True),
        state=OrderSettings.send_settings,
    )
    dp.register_callback_query_handler(
        change_gender,
        text="change_gender",
        state=OrderSettings.send_settings,
    )
    dp.register_callback_query_handler(
        change_own_photo,
        text="change_own_photo",
        state=OrderSettings.send_settings,
    )
    dp.register_message_handler(
        send_settings_photo_group,
        is_media_group=True,
        content_types=["photo", "document", "text"],
        state=OrderSettings.send_settings,
    )
    dp.register_message_handler(
        send_settings_photo,
        content_types=["photo", "document", "text"],
        state=OrderSettings.send_settings,
    )
