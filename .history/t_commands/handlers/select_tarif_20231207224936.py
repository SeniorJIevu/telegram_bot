import asyncio
import concurrent.futures
import copy
import random

import aiofiles
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from constants import *
from constants import env
from keyboards import *
from references.references import REFERENCES
from t_commands.db import *


class TarifStart(StatesGroup):
    send_select_tarif = State()


async def get_time(count_in_queue):
    time_sec = count_in_queue * 15
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


def copy_deepcopy(gender, history_image_links):
    user_references = copy.deepcopy(
        REFERENCES.get("BOYS_JPG" if gender == "male" else "GIRLS_JPG")
    )
    if history_image_links != {}:
        for link in history_image_links:
            try:
                link_split = link.split("/")
                if link in user_references.get(link_split[2]):
                    user_references.get(link_split[2]).remove(link)
                if not user_references.get(link_split[2]):
                    user_references.pop(link_split[2])
            except:
                continue
    return user_references


async def get_user_references_remaining(user_id, db: asyncpg.pool.Pool):
    """
    Возвращает список доступных референсов user_references,
    а также ссылку
    """

    user = await get_user_information(user_id, db)
    if not user:
        await bot.send_message(
            chat_id=user_id,
            text="""Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    gender, current_user_image_link = user.get("gender"), user.get(
        "image_link"
    )
    history_image_links = await get_user_history_image_links(
        user_id, current_user_image_link, db
    )

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        user_references = await loop.run_in_executor(
            pool, copy_deepcopy, *(gender, history_image_links)
        )

    return user_references, current_user_image_link


async def add_to_queue(message, request_type, count_photo, db):
    """Функция добавляет задачи на генерацию фото в очередь."""

    id_in_user_images = await add_pending_image_request(
        message.chat.id, request_type, db
    )
    if not id_in_user_images:
        return
    id_in_history_collage_links = None
    if request_type in [

        IMAGE_FOR_REFERAL,
        IMAGE_COLLAGE_50,

    ]:
        id_in_history_collage_links = await add_history_collage_links(
            message.chat.id, request_type, id_in_user_images, db
        )
    (
        user_references,
        current_user_image_link,
    ) = await get_user_references_remaining(message.chat.id, db)
    if len(user_references) >= count_photo:
        keys_choice = random.sample(list(user_references), k=count_photo)
        image_reference_link_list = []
        for n, item in enumerate(keys_choice):
            image_reference_link_list.append(
                random.choices(user_references.get(item))[0]
            )
        image_reference_links = ";;".join(image_reference_link_list)
        await add_user_image_request_to_queue(
            message.chat.id,
            n + 1,
            id_in_user_images,
            image_reference_links,
            current_user_image_link,
            count_photo,
            request_type,
            db,
            id_in_history_collage_links,
        )
        if (
            request_type != IMAGE_COLLAGE_50

        ):
            await message.answer(
                """Бот принял заявку 🫡
Пришлем фотографии как только будут готовы 💪
""",
                reply_markup=keyboard_select_other_tarif,
            )




@rate_limit(5)
async def send_tarif_turbo(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    user = await get_user_information(message.chat.id, db)
    if not user:
        await message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    admin_id = env["ADMIN_ID"].split(",")
    gender, current_user_image_link = user.get("gender"), user.get(
        "image_link"
    )
    price = types.LabeledPrice(label="50 аватарок", amount=TURBO_RUB)
    photo_url = (
        "https://telegra.ph/file/1c36e0ad9b0b148979836.jpg"
        if gender == "male"
        else "https://telegra.ph/file/a00b0b8d043dcd634d395.jpg"
    )
    text = f"""Тариф Супер
Получить 50 аватарок в течение нескольких часов

В отличие от бесплатного тарифа ты получишь аватарки в 50 разных стилях.
На коллаже снизу показаны стили твоих будущих аватарок
    """
    (
        user_references,
        current_user_image_link,
    ) = await get_user_references_remaining(message.chat.id, db)
    if len(user_references) >= COUNT_PHOTO_TURBO:
        await bot.send_invoice(
            message.chat.id,
            title=AVA_50,
            description=text,
            provider_token=env["TELEGRAM_PAYMENTS_TOKEN"],
            currency="rub",
            photo_url=photo_url,
            photo_height=1280,  # !=0/None, иначе изображение не покажется
            photo_width=1187,
            photo_size=800,
            is_flexible=False,  # True если конечная цена зависит от способа доставки
            protect_content=True,
            prices=[price],
            start_parameter="time-machine-example123",
            payload="tarif-turbo",
            provider_data='{"receipt": {"items": [{"description": "50 аватарок", "quantity": "1", "amount": {"value": "200.00", "currency": "RUB"}, "vat_code": 1}], "customer": {"email": "best.web.partners@gmail.com"}}}',
        )
        if str(message.chat.id) in admin_id:
            await message.answer(
                "Только для админа",
                reply_markup=keyboard_admin_50_ava,
            )
        await message.answer(
            "☝️",
            reply_markup=keyboard_select_other_tarif,
        )
    else:
        await message.answer(
            f"""Осталось аватарок: { len(user_references) }

К сожалению для текущего Вашего фото и данного тарифа нехватает аватарок ☹️

Но вы можете обновить свое фотов в /settings и получить аватарки уже с новым фото 😌👍
            """,
            reply_markup=keyboard_select_other_tarif,
        )



@rate_limit(5)
async def send_select_tarif(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    text = "Выбери тариф"

    keyboard = (
        keyboard_select_tarif2
    )
    photo_tarif = (
        "images/photo_tarif_2.png"

    )
    async with aiofiles.open(photo_tarif, mode="rb") as photo:
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
        )


async def get_50_avatarok(call: types.CallbackQuery, db: asyncpg.pool.Pool):
    count_photo = COUNT_PHOTO_TURBO
    await add_to_queue(call.message, IMAGE_PAID, count_photo, db)





def register_select_tarif(dp: Dispatcher):

    dp.register_message_handler(
        send_tarif_turbo,
        Text(equals=SEND_TARIF_TURBO, ignore_case=True),
        state=TarifStart.send_select_tarif,
    )

    dp.register_message_handler(
        send_select_tarif,
        Text(equals=SEND_SELECT_OTHER_TARIF, ignore_case=True),
        state=TarifStart.send_select_tarif,
    )
    dp.register_message_handler(
        send_select_tarif,
        Text(equals=SEND_SELECT_TARIF, ignore_case=True),
        state=TarifStart.send_select_tarif,
    )
    dp.register_callback_query_handler(
        get_50_avatarok,
        text="get_50_avatarok",
        state=TarifStart.send_select_tarif,
    )

