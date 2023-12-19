import datetime as dt
import logging

import asyncpg
from aiogram import types
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from bot_sheduler import *
from constants import *
from t_commands.handlers.select_tarif import add_to_queue
from t_commands.ref_system import send_ready_referal_message


async def get_time(count_in_queue):
    time_sec = count_in_queue * 120
    time_hours = time_sec // 3600
    time_sec_ost = time_sec % 3600
    time_min = time_sec_ost // 60
    time_sec_ost = time_min

    if time_hours == 0 and time_min == 0:
        return f"{time_sec} секунд"
    if time_hours == 0 and time_min != 0:
        return f"примерно {time_min} мин. {time_sec % 60} секунд"
    if time_hours != 0:
        return (
            f"примерно {time_hours} ч. {time_min} мин. {time_sec % 60} секунд"
        )


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(
    pre_checkout_q: types.PreCheckoutQuery, db: asyncpg.pool.Pool
):
    """
    Необходимо для подтверждения наличия товара,
    когда пользователь совершает покупку. В нашем случае товар всегда есть.
    """
    user = await get_user_information(pre_checkout_q.from_user.id, db)
    if not user:
        text = """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """
        await bot.answer_pre_checkout_query(
            pre_checkout_q.id, ok=False, error_message=text
        )
        await bot.send_message(
            chat_id=pre_checkout_q.from_user.id,
            text=text,
        )
        return
    if (
        pre_checkout_q.invoice_payload == IMAGE_COLLAGE_50
        or pre_checkout_q.invoice_payload == IMAGE_COLLAGE_100
    ):
        collage_link = await is_collage_exist(
            pre_checkout_q.from_user.id, pre_checkout_q.invoice_payload, db
        )
        if not collage_link:
            text = """Данный товар отсутствует в базе и уже не актуален.☹️
        
Чтобы получить аватарки, пожалуйста выберите тариф 👇🏼
        """
            await bot.answer_pre_checkout_query(
                pre_checkout_q.id, ok=False, error_message=text
            )
            await bot.send_message(
                chat_id=pre_checkout_q.from_user.id,
                text=text,
            )
            return
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(
    content_types=types.ContentTypes.SUCCESSFUL_PAYMENT, state="*"
)
async def successful_payment(message: types.Message, db: asyncpg.pool.Pool):
    """Событие вызывается после успешной оплаты."""

    count_in_queue = await check_free_queue(IMAGE_PAID, db)
    user = await get_user_information(message.chat.id, db)
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    await add_to_payment_table(
        user,
        message.successful_payment.invoice_payload,
        now_formatted,
        message.successful_payment.total_amount / 100,
        db,
    )
    if (
        message.successful_payment.invoice_payload == TARIF_TURBO
        or message.successful_payment.invoice_payload == TARIF_PREMIUM
    ):
        if message.successful_payment.invoice_payload == TARIF_TURBO:
            count_photo = COUNT_PHOTO_TURBO
        else:
            count_photo = COUNT_PHOTO_PREM
        text = f"""Время ожидания — {await get_time(len(count_in_queue)+1)} ⏳
Отправим аватарок — {count_photo}
Очередь — {len(count_in_queue)} человек.
        """
        await bot.send_message(
            message.chat.id, text, reply_markup=keyboard_select_other_tarif
        )
        await add_to_queue(message, IMAGE_PAID, count_photo, db)
    if (
        message.successful_payment.invoice_payload == IMAGE_COLLAGE_50
        or message.successful_payment.invoice_payload == IMAGE_COLLAGE_100
    ):
        if message.successful_payment.invoice_payload == IMAGE_COLLAGE_50:
            user_image_id, image_links = await get_paid_collage_target_links(
                message.chat.id, IMAGE_COLLAGE_50, db
            )
        else:
            user_image_id, image_links = await get_paid_collage_target_links(
                message.chat.id, IMAGE_COLLAGE_100, db
            )
        image_links = image_links.split(";;")
        last = False
        for i, image_link in enumerate(image_links):
            if (i + 1) % 10 != 0 and (i + 1) != len(image_links):
                continue
            if i + 1 == len(image_links):
                last = True
            await send_request_message(
                message, image_links[i - 9 : i + 1], last, bot=message.bot
            )
        if last:
            await change_user_images_status_sent(user_image_id, SENT, db)
        ref_collage_link = await send_ready_referal_message(
            message.chat.id, user_image_id, db
        )
        try:
            for i in image_links:
                await MINIO_CLIENT.remove_object("shawa", i)
            await MINIO_CLIENT.remove_object("shawa", ref_collage_link)
        except Exception as e:
            logging.error(
                "Ошибка в successful_payment MINIO_CLIENT.remove_object", e
            )
    collage_link = await is_pending_collage(message.chat.id, db)
    if collage_link:
        if collage_link.get("image_collage_link"):
            if collage_link["image_tarif"] == IMAGE_COLLAGE_50:
                await send_collage_message(
                    message.chat.id,
                    collage_link["image_collage_link"],
                    COUNT_PHOTO_TURBO,
                )
            else:
                await send_collage_message(
                    message.chat.id,
                    collage_link["image_collage_link"],
                    COUNT_PHOTO_PREM,
                )
        return
    await add_to_queue(message, IMAGE_COLLAGE_100, COUNT_PHOTO_PREM, db)


class DatabaseMiddleware(LifetimeControllerMiddleware):
    def __init__(self):
        super().__init__()
        self.pool = None

    async def pre_process(self, obj, data, *args):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                user=env["POSTGRES_USER"],
                password=env["POSTGRES_PASSWORD"],
                database=env["DB_NAME"],
                host="127.0.0.1",
            )
        data["db"] = self.pool
        try:
            if obj.pre_checkout_query:
                await pre_checkout_query(obj.pre_checkout_query, self.pool)
        except AttributeError:
            pass

    async def post_process(self, obj, data, *args):
        ...

    def get_pool(self):
        return self.pool
