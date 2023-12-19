import io
import logging
import uuid
from typing import List
import time
import aiofiles
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import (
    BotBlocked,
    UserDeactivated,
    ChatNotFound,
)
from functools import wraps
from keyboards import *
from t_commands.db import *
from t_commands.handlers.select_tarif import TarifStart
from t_commands.ref_system import add_to_queue_ref









button_clicks = {}
sent_messages = {}  # Добавлена инициализация переменной
cooldown_time = 10  # Время ожидания после отправки сообщения в секундах

def prevent_double_click(func):
    @wraps(func)
    async def wrapper(callback_query: types.CallbackQuery, state, db):
        user_id = callback_query.from_user.id

        # Если для данного пользователя уже были нажаты кнопки, проверяем статус
        if user_id in button_clicks:
            button_info = button_clicks[user_id]
            if button_info['timestamp'] + cooldown_time > time.time():
                # Пользователь слишком быстро нажал на кнопку
                await callback_query.answer("Не так быстро, пожалуйста :)")
                return
            elif button_info['message_id'] and button_info['message_id'] in sent_messages:
                # Для этого пользователя уже было отправлено сообщение, проверяем, прошло ли достаточно времени
                await callback_query.answer("Вы уже отправили сообщение, подождите ответа :)")
                return

        # Если кнопка не была нажата или прошло достаточно времени, вызываем функцию-обработчик
        await func(callback_query, state, db)

        # Обновляем информацию о нажатии
        button_clicks[user_id] = {
            'timestamp': time.time(),
            'message_id': None,  # Идентификатор отправленного сообщения
        }

        # Добавляем идентификатор отправленного сообщения в словарь отправленных сообщений
        sent_message_id = callback_query.message.message_id if callback_query.message else None
        if sent_message_id:
            sent_messages[sent_message_id] = time.time()

        # Проверяем и удаляем старые записи в словаре отправленных сообщений
        current_time = time.time()
        for msg_id, timestamp in list(sent_messages.items()):
            if current_time - timestamp > cooldown_time:
                del sent_messages[msg_id]

    return wrapper






class OrderStart(StatesGroup):
    send_start = State()
    send_continue = State()
    send_gender = State()
    send_photo = State()



async def send_start(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    text = """Привет ✌

Я создам аватарки по твоим фото бесплатно

Подпишись на @ava_dream_news и возвращайся
    """
    try:
        await bot.send_chat_action(message.chat.id, "typing")
        ref_code = uuid.uuid4().hex
        args = message.get_args()
        refferer_code, refferer_id, send_ref = await check_referal_exists(
            args, message.chat.id, db
        )
        is_user_exist = await write_user_to_db(
            message, ref_code, db, refferer_code
        )
        await state.set_state(OrderStart.send_start.state)
        if is_user_exist:
            text = "Снова рады тебя видеть :)"
            await message.answer(
                text,
                reply_markup=keyboard_send_start,
            )
            await state.set_state(OrderStart.send_photo.state)
        else:
            async with aiofiles.open(
                "images/photo_start.jpg", mode="rb"
            ) as photo:
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard_send_start,
                )
            await state.set_state(OrderStart.send_continue.state)    
        if refferer_code and send_ref:
            await add_to_queue_ref(
                refferer_id, "image_for_referal", COUNT_PHOTO_FOR_REFERAL, db
            )
    except (UserDeactivated, ChatNotFound, BotBlocked) as e:
        print(f"Пользователь c id: {message.chat.id} заблокировал бота")


async def send_continue(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    print('send_continue')
    try:
        text = "Выберите свой гендер"

        if call.data.lower() != "продолжить 👉🏻":
            await call.message.answer(
                "Пожалуйста, нажмите кнопку продолжить ниже 👇🏼"
            )
            return
        await call.message.answer(text, reply_markup=keyboard_select_gender)
        await state.set_state(OrderStart.send_continue.state)
    except (UserDeactivated, ChatNotFound, BotBlocked) as e:
        print(f"Пользователь c id: {call.message.chat.id} заблокировал бота")

@dp.callback_query_handler(state=OrderStart.send_continue)
@prevent_double_click
async def send_gender(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    print('send_gender')
    image_count = await get_user_image_count(call.message, db)
    if image_count >= 1:
        await state.set_state(TarifStart.send_select_tarif.state)
        await click_continue(call, state, db)
        return
    if call.data.lower() not in ("🚺 женский", "🚹 мужской"):
        await call.message.answer(
            (
                "Чтобы продолжить, выберите пожалуйста свой пол, "
                "нажав одну из кнопок ниже 👇🏼"
            ),
            reply_markup=keyboard_select_gender,
        )

        return
    if call.data.lower() == "🚺 женский":
        await user_update_gender(call.message.chat.id, "female", db)
    else:
        await user_update_gender(call.message.chat.id, "male", db)
    text = """Загрузите свою фотографию
👍 Требования к фотографии:
- Четкая, в хорошем качестве селфи
- Фотография должна быть именно селфи с одним человеком

👎 Какие фото нельзя загружать:
- Групповое фото
- Животных
- Детей до 18 лет
- Фото в полный рост
- Обнаженные фото
- В солнцезащитных очках
- Фото, где лицо закрыто любыми предметами
- Нечеткие и смазанные фото
- Видео и "кружочки"
- Фото без сжатия

После ознакомления, загрузи 1 фото
    """
    async with aiofiles.open("images/send_photo.jpg", mode="rb") as photo:
        await call.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=types.ReplyKeyboardRemove(),
        )
        print(call.message.content_type)
        
    await state.set_state(OrderStart.send_gender.state)
    

async def send_photo_group(
    message: types.Message,
    album: List[types.Message],
    state: FSMContext,
    db: asyncpg.pool.Pool,
):
    print('photo_group')
    image_count = await get_user_image_count(message, db)
    if (
        message.content_type == "text"
        and message.text.lower() == "продолжить 👉🏻"
    ):
        if image_count == 0:
            await message.answer(
                "Пожалуйста отправляйте данные в виде изображений!"
            )
        await click_continue(message, state, db)
    if message.content_type != "photo":
        if image_count == 0:
            await message.answer(
                "Пожалуйста отправляйте данные в виде изображений!"
            )
        text = """Пожалуйста отправляйте данные в виде изображений!

Нажмите кнопку «Продолжить 👉🏻»
        """
        await message.answer(text, reply_markup=keyboard_send_start)
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = types.KeyboardButton(text="Продолжить 👉🏻")
    keyboard.add(button_1)
    if image_count >= 1:
        await message.answer(
            "Чтобы продолжить нажмите кнопку ниже 👇🏼", reply_markup=keyboard
        )
        await state.set_state(OrderStart.send_photo.state)
        return
    last_msg = await message.answer("Обрабатываем изображения... ⏳")
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

        image_count += 1
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
        message, USER_IMAGES_CHECK_PACK, image_path_str, db
    )

async def send_photo(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    print('photo')
    image_count = await get_user_image_count(message, db)
    if (
        message.content_type == "text"
        and message.text.lower() == "продолжить 👉🏻"
    ):
        if image_count == 0:
            await message.answer(
                "Пожалуйста отправляйте данные в виде изображений!"
            )
        await click_continue(message, state, db)
        return

    if message.content_type != "photo":
        if image_count == 0:
            await message.answer(
                "Пожалуйста отправляйте данные в виде изображений!"
            )
            return
        text = """Пожалуйста отправляйте данные в виде изображений!

Нажмите кнопку «Продолжить 👉🏻»
        """
        await message.answer(text, reply_markup=keyboard_send_start)
        return

    if image_count >= 1:
        await message.answer(
            "Чтобы продолжить нажмите кнопку ниже 👇🏼",
            reply_markup=keyboard_send_start,
        )
        await state.set_state(OrderStart.send_photo.state)
        return
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
            "Ошибка в send_photo MINIO_CLIENT.get_object",
            e,
        )
    await add_to_check_user_image_queue(
        message, USER_IMAGE_CHECK, new_file_path, db
    )


@dp.callback_query_handler(state=OrderStart.send_continue)
@prevent_double_click
async def click_continue(
    call: types.CallbackQuery, state: FSMContext, db: asyncpg.pool.Pool
):
    print('click_continue')
    if (
        call.data.lower() != "продолжить 👉🏻"
    ) and call.data.lower() not in ("🚺 женский", "🚹 мужской"):
        await call.message.answer(
            "Чтобы продолжить нажмите кнопку ниже 👇🏼",
            reply_markup=keyboard_select_tarif1,
        )
        return
    if_use_free_tarif = await check_if_use_free_tarif(call, db)
    keyboard = (
        keyboard_select_tarif2 if if_use_free_tarif else keyboard_select_tarif1
    )
    photo_tarif = (
        "images/photo_tarif_2.png"
        if if_use_free_tarif
        else "images/photo_tarif.png"
    )
    async with aiofiles.open(photo_tarif, mode="rb") as photo:
        await call.message.answer_photo(
            photo=photo,
            caption="Выбери тариф ☝️",
            reply_markup=keyboard,
        )
    await state.set_state(TarifStart.send_select_tarif.state)


async def cmd_cancel(
    message: types.Message, state: FSMContext, db: asyncpg.pool.Pool
):
    await state.finish()
    await message.answer(
        "Действие отменено", reply_markup=types.ReplyKeyboardRemove()
    )


def register_handler_start(dp: Dispatcher):
    dp.register_message_handler(send_start, commands="start", state="*")
    dp.register_callback_query_handler(send_continue, state=OrderStart.send_start)
    dp.register_callback_query_handler(send_gender, state=OrderStart.send_continue)
    dp.register_message_handler(
        send_photo_group,
        is_media_group=True,
        content_types=["photo", "document", "text"],
        state=OrderStart.send_gender,
    )
    dp.register_message_handler(
        send_photo,
        content_types=["photo", "document", "text"],
        state=OrderStart.send_gender,
    )

    dp.register_callback_query_handler(
        click_continue,
        state=OrderStart.send_photo,
    )
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(
        cmd_cancel, Text(equals="отмена", ignore_case=True), state="*"
    )
