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



async def settings_call(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    print(call.data, 'Настройки2')
    user = await get_user_information(call.message.chat.id, db)
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
            await call.message.answer_photo(
                photo=source_path,
                caption=f"""Ваше текущее фото ☝️
                
Ваш гендер: {gender}

Реферальная ссылка: {env["BOT_NAME"]}?start={user["ref_code"]}
                """,
                reply_markup=keyboard_settings,
            )
        except Exception as e:
            await call.message.answer(
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
    await call.message.answer(
        "Вы можете заменить Вашу текущую фотографию на новую, изменить пол, либо поделиться реферальной ссылкой с другом и получить 5 аватарок бесплатно 😌",
        reply_markup=keyboard_back_to_tarif,
    )
    

