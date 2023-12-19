import asyncio
import concurrent.futures
import copy
import random

import aiofiles
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from constants import *
from constants import env
from keyboards import *
from references.references import REFERENCES
from t_commands.db import *
from t_commands.handlers.settings_call import settings

class TarifStart(StatesGroup):
    send_select_tarif = State()
    send_settings_rarif = State()


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


async def add_to_queue(call, request_type, count_photo, db):
    """Функция добавляет задачи на генерацию фото в очередь."""
    result_from_check = await check_user_photo(call, db)
    
    id_in_user_images = await add_pending_image_request(
        call.chat.id, request_type, db
    )
    if not id_in_user_images:
        return
    id_in_history_collage_links = None
    if request_type in [
        
        IMAGE_FOR_REFERAL,
        IMAGE_COLLAGE_50,
   
    ]:
        id_in_history_collage_links = await add_history_collage_links(
            call.chat.id, request_type, id_in_user_images, db
        )
    (
        user_references,
        current_user_image_link,
    ) = await get_user_references_remaining(call.chat.id, db)
    first_value = next(iter(user_references.values()), None)

    if len(first_value)-len(result_from_check) >= 10:

            try:
                
               
                user_reference = {k: [j for j in v if j not in result_from_check] for k, v in user_references.items()}
                print('user_reference', user_reference)

                keys_choice = list(user_reference.keys())

                image_reference_link_list = []
                for n, item in enumerate(keys_choice):
                    image_reference_link_list.append(
                        user_reference.get(item)
                    )

                

                image_reference_links = ";;".join(image_reference_link_list[0][:10])
                
                await add_user_image_request_to_queue(
                    call.chat.id,
                    n + 10,
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
                    await call.answer(
                        text = """Ваша заявка в очереди на генерацию 👍
Пришлем картинки как только будут готовы 😈
        """,
                        
                    )
              
            except Exception as err:
                print(f'ERROR EQUE {err}')

@dp.callback_query_handler(lambda el: el.data == "🔞 10 сочных генераций: 400 RUB 🔞", state=TarifStart.send_select_tarif)
async def send_tarif_turbo(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    one_users_queue = await one_users_queues(call, db)
    print('one_users_queue', one_users_queue)
    result_from_check = await check_user_photo(call, db)
    await call.answer(cache_time=20)
    user = await get_user_information(call.message.chat.id, db)
    if not user:
        await call.message.answer(
            """Пользователь не найден.☹️
        
Пожалуйста пройдите авторизацию, нажав команду /start
        """,
        )
        return
    admin_id = env["ADMIN_ID"].split(",")
    gender, current_user_image_link = user.get("gender"), user.get(
        "image_link"
    )
    price = types.LabeledPrice(label="10 генераций", amount=TURBO_RUB)
    photo_url = (
        "https://telegra.ph/file/9ca78f0a789ccbf7d5647.png"
    )
    text = f"""🔞10 генераций 🔞
Воплоти свои желания 😈
    """
    (
        user_references,
        current_user_image_link,
    ) = await get_user_references_remaining(call.message.chat.id, db)
   
    first_value = next(iter(user_references.values()), None)
    print(len(first_value), len(result_from_check), len(first_value)-len(result_from_check), 'fff')
    if one_users_queue:
        if len(first_value)-len(result_from_check) >= 10:
            await bot.send_invoice(
                call.message.chat.id,
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
                provider_data='{"receipt": {"items": [{"description": "10 генераций", "quantity": "1", "amount": {"value": "400.00", "currency": "RUB"}, "vat_code": 1}], "customer": {"email": "best.web.partners@gmail.com"}}}',
            )
            if str(call.message.chat.id) in admin_id:
                await call.message.answer(
                    "Только для админа",
                    reply_markup=keyboard_admin_50_ava,
                )
        else:
            await call.message.answer(
                f"""

    К сожалению для текущего Вашего фото и данного тарифа нехватает аватарок ☹️

    🔞 Но вы можете обновить свое фотов в /settings и начать генерацию 🔞
                """,
                reply_markup=keyboard_select_other_tarif,
            )
    else:
            await call.message.answer(
                f"""

    🔞 Ваш запрос уже обрабатывается, дождитесь окончания и Вы снова сможете отправить запросу на генерацию 🔞
                """,
                
            )




async def send_select_tarif(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    await call.answer(cache_time=20)
    if call.data == SETTINGS:
        await settings(call.message, state, db)
    else:    
        text = "<i><b>Выбери тариф 👇</b></i>"
        
        
        keyboard = (
            keyboard_select_tarif2
        )

        await call.message.answer(

                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        

async def get_50_avatarok(call: types.CallbackQuery, db: asyncpg.pool.Pool):
    count_photo = COUNT_PHOTO_TURBO
    await add_to_queue(call.message, IMAGE_PAID, count_photo, db)




def register_select_tarif(dp: Dispatcher):

    dp.register_callback_query_handler(
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
