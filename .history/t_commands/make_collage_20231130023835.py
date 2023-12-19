import io
import logging

import aiohttp
from aiogram import types
from aiogram.utils.exceptions import BotBlocked

from constants import *
from t_commands.db import *
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware




async def get_object_from_minio(link, session):
    try:
        source_path_temp = await MINIO_CLIENT.get_object(
            BUCKET_NAME, link, session
        )
        source_path = io.BytesIO(await source_path_temp.read())
        return source_path_temp, source_path
    except:
        await get_object_from_minio(link, session)
        print(f"Ошибка в get_object_from_minio")


async def send_collage_message(chat_id, collage_link, image_count):
    text = f"""Получи {image_count} аватарок мгновенно❗️

Или сделай новые аватарки. Акция действует ровно сутки❗️
    """
    async with aiohttp.ClientSession() as session:
        try:
            source_path_temp, source_path = await get_object_from_minio(
                collage_link, session
            )
            await bot.send_photo(
                chat_id=chat_id,
                photo=source_path,
                caption="",
            )
            if image_count <= 50:
                title = AVA_50
                price = types.LabeledPrice(label=AVA_50, amount=TURBO_RUB)
                payload = IMAGE_COLLAGE_50
                provider_data = '{"receipt": {"items": [{"description": "50 аватарок", "quantity": "1", "amount": {"value": "200.00", "currency": "RUB"}, "vat_code": 1}], "customer": {"email": "best.web.partners@gmail.com"}}}'
            else:
                title = AVA_100
                price = types.LabeledPrice(label=AVA_100, amount=PREMIUM_RUB)
                payload = IMAGE_COLLAGE_100
                provider_data = '{"receipt": {"items": [{"description": "100 аватарок", "quantity": "1", "amount": {"value": "300.00", "currency": "RUB"}, "vat_code": 1}], "customer": {"email": "best.web.partners@gmail.com"}}}'
            await bot.send_invoice(
                chat_id=chat_id,
                title=title,
                description=text,
                provider_token=env["TELEGRAM_PAYMENTS_TOKEN"],
                currency="rub",
                photo_url=None,
                photo_height=None,  # !=0/None, иначе изображение не покажется
                photo_width=None,
                photo_size=None,
                is_flexible=False,  # True если конечная цена зависит от способа доставки
                protect_content=True,
                prices=[price],
                start_parameter="time-machine-example",
                payload=payload,
                provider_data=provider_data,
            )
        except BotBlocked:
            print(f"Пользователь c id: {chat_id} заблокировал бота")
        except Exception as e:
            logging.error("Возникла ошибка в send_collage_message", e)
        finally:
            source_path_temp.close()
            await source_path_temp.release()
            await session.close()
