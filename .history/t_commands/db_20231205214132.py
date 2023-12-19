import datetime as dt
from aiogram import types
import asyncpg

from constants import *


async def connect_to_db():
    db = await asyncpg.connect(
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        database=env["DB_NAME"],
        host="127.0.0.1",
    )
    return db


async def write_user_to_db(message, ref_code, db: asyncpg.pool.Pool, ref_id):
    """Добавляет пользователя в базу, по команде /start."""

    try:
        now = dt.datetime.now()
        now_formatted = now.strftime(DATETIME_FORMAT)
        async with db.acquire() as connection:
            async with connection.transaction():
                select_id = await connection.fetchval(
                    "SELECT id FROM users WHERE user_id = $1",
                    message.chat.id,
                )
                if select_id:
                    return True

                await connection.execute(
                    """INSERT INTO users(
                        user_id, 
                        referrer_id,
                        last_login, 
                        username, 
                        first_name, 
                        last_name, 
                        last_msg, 
                        join_date,
                        ref_code) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    message.chat.id,
                    ref_id,
                    now_formatted,
                    (message.chat.username if message.chat.username else "-"),
                    (
                        message.chat.first_name
                        if message.chat.first_name
                        else "-"
                    ),
                    (
                        message.chat.last_name
                        if message.chat.last_name
                        else "-"
                    ),
                    message.text,
                    now_formatted,
                    ref_code,
                )
                return False
    except Exception as e:
        await bot.send_message(
            612063160,
            (
                f"Ошибка при добавлении (INSERT) данных в базе "
                f"Пользователь: {message.chat.id}\n{e}"
            ),
        )
        return False


async def user_update_gender(user_id, gender, db: asyncpg.pool.Pool):
    """Обновляет пол пользователя в таблице user."""

    async with db.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "UPDATE users SET gender=$1 WHERE user_id = $2",
                gender,
                user_id,
            )
        return True


async def get_user_information(user_id, db: asyncpg.pool.Pool):
    """
    Возвращает информацию о пользователе из таблицы user.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            select_id = await connection.fetchrow(
                """SELECT * FROM users 
                JOIN user_image_links 
                ON users.user_id = user_image_links.user_id 
                WHERE users.user_id = $1""",
                user_id,
            )

            return select_id


async def con_get_user_information(user_id):
    """
    Возвращает информацию о пользователе из таблицы user.
    """

    connection = await connect_to_db()
    try:
        select_id = await connection.fetchrow(
            """SELECT * FROM users 
            JOIN user_image_links 
            ON users.user_id = user_image_links.user_id 
            WHERE users.user_id = $1""",
            user_id,
        )
    finally:
        await connection.close()
    return select_id


async def get_user_image_count(message, db: asyncpg.pool.Pool):
    """
    Возвращает количество фотографий пользователя, которые собственно
    пользователь загрузил.
    """
    if message == types.CallbackQuery:
        async with db.acquire() as connection:
            async with connection.transaction():
                select_id = await connection.fetchval(
                    "SELECT user_images FROM users WHERE user_id = $1",
                    message.from_id,
                )

                return int(select_id) if select_id is not None else 0
    else:
        async with db.acquire() as connection:
            async with connection.transaction():
                select_id = await connection.fetchval(
                    "SELECT user_images FROM users WHERE user_id = $1",
                    message.from_id,
                )

                return int(select_id) if select_id is not None else 0
        

async def get_user_history_image_links(
    user_id, current_user_image_link, db: asyncpg.pool.Pool
):
    """
    Возвращает множество ссылок на рефференсы которые
    уже использованы пользователем.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query = """
            SELECT image_reference_link 
            FROM history_image_links 
            WHERE user_id=$1 AND user_image_link=$2
            """
            select_id = await connection.fetch(
                query, user_id, current_user_image_link
            )
    if select_id == []:
        return select_id
    image_links = []
    for id in set(select_id):
        select_id = id.get("image_reference_link").split(";;")
        image_links.extend(select_id)
    return set(image_links)


async def get_paid_collage_target_links(
    user_id, image_tarif, db: asyncpg.pool.Pool
):
    """
    Возвращает массив ссылок на готовые изображения.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select_id = """
            SELECT id 
            FROM user_images 
            WHERE user_id=$1 
            AND image_tarif=$2
            AND status=$3
            AND is_collage_sended=$4
            """
            select_id = await connection.fetchval(
                query_select_id, user_id, image_tarif, READY, 1
            )

            query_select_links = """
            SELECT image_target_link 
            FROM history_image_links 
            WHERE image_request_id=$1
            """
            select_links = await connection.fetch(
                query_select_links, select_id
            )

            return select_id, select_links[0]["image_target_link"]


async def is_pending_collage(user_id, db: asyncpg.pool.Pool):
    """
    Возвращает ссылку на колаж, который имеет статус pending или ready
    (то есть готов и не продан).
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select_links = """
            SELECT image_collage_link, user_images_id, image_tarif
            FROM history_collage_links 
            JOIN user_images 
            ON history_collage_links.user_images_id = user_images.id 
            WHERE history_collage_links.user_id=$1 
            AND (user_images.status=$2 OR user_images.status=$3)
            AND (user_images.is_collage_sended=$4 OR user_images.is_collage_sended=$5)
            """
            select_links = await connection.fetchrow(
                query_select_links, user_id, READY, PENDING, 0, 1
            )

            return select_links if select_links else False


async def is_ready_collage(user_id, user_images_id):
    """
    Возвращает ссылку на колаж, который имеет статус ready
    (то есть готов и не продан).
    """

    connection = await connect_to_db()
    try:
        query_select_links = """
        SELECT image_collage_link 
        FROM history_collage_links 
        WHERE user_id=$1 
        AND user_images_id=$2
        """
        select_links = await connection.fetchrow(
            query_select_links, user_id, user_images_id
        )
    finally:
        await connection.close()
    return select_links if select_links else False


async def con_get_collage_link(user_images_id):
    """
    Возвращает ссылку на колаж, по image_id
    """

    connection = await connect_to_db()
    try:
        query_select_links = """
        SELECT image_collage_link 
        FROM history_collage_links 
        WHERE user_images_id=$1 
        """
        select_links = await connection.fetchrow(
            query_select_links, user_images_id
        )
    finally:
        await connection.close()
    return select_links if select_links else False


async def get_collage_link(user_images_id, db: asyncpg.pool.Pool):
    """
    Возвращает ссылку на колаж, по image_id
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select_links = """
            SELECT image_collage_link 
            FROM history_collage_links 
            WHERE user_images_id=$1 
            """
            select_links = await connection.fetchrow(
                query_select_links, user_images_id
            )

            return select_links if select_links else False


async def is_collage_exist(user_id, collage_type, db: asyncpg.pool.Pool):
    """
    Возвращает ссылку на колаж, который имеет статус READY
    (то есть не продан). Проверка перед оплатой колажа.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select_links = """
            SELECT image_collage_link, user_images_id 
            FROM history_collage_links 
            JOIN user_images 
            ON history_collage_links.user_images_id=user_images.id 
            WHERE history_collage_links.user_id=$1 
            AND history_collage_links.collage_type=$2
            AND user_images.status=$3
            AND user_images.is_collage_sended=$4
            """
            select_links = await connection.fetchrow(
                query_select_links, user_id, collage_type, READY, 1
            )

            return select_links if select_links else False


async def get_image_target_links(image_request_id, db: asyncpg.pool.Pool):
    """
    Возвращает массив ссылок на готовые изображения для создания коллажа.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select_links = """
            SELECT image_target_link 
            FROM history_image_links 
            WHERE image_request_id=$1
            """
            select_links = await connection.fetch(
                query_select_links, image_request_id
            )

            return select_links[0]["image_target_link"].split(";;")


async def con_get_image_target_links(image_request_id):
    """
    Возвращает массив ссылок на готовые изображения для создания коллажа.
    """

    connection = await connect_to_db()
    try:
        query_select_links = """
        SELECT image_target_link 
        FROM history_image_links 
        WHERE image_request_id=$1
        """
        select_links = await connection.fetch(
            query_select_links, image_request_id
        )
    finally:
        await connection.close()
    return select_links[0]["image_target_link"].split(";;")


async def set_user_image_links(message_from_id, path, image_count):
    """
    Функция добавляет ссылки на фотографии пользователя в
    таблицу user_image_links, а также обновляет количество загруженных
    фотографий в таблице user.
    """

    connection = await connect_to_db()
    try:
        query_insert_link = """
        INSERT INTO user_image_links (user_id, image_link) 
        VALUES ($1, $2)
        """
        await connection.execute(query_insert_link, message_from_id, path)

        query_update_count = """
        UPDATE "users" SET user_images=$1 WHERE user_id=$2
        """
        await connection.execute(
            query_update_count, image_count, message_from_id
        )
    finally:
        await connection.close()
    return True


async def add_to_payment_table(
    user, image_tarif, datetime, amount, db: asyncpg.pool.Pool
):
    """
    Функция добавляет запись в payment_table после успешной оплаты.
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_insert_link = """
            INSERT INTO payment_table (user_id, referal_code, amount, image_tarif, datetime) 
            VALUES ($1, $2, $3, $4, $5)
            """
            await connection.execute(
                query_insert_link,
                user["user_id"],
                user["referrer_id"],
                amount,
                image_tarif,
                datetime,
            )

            return True


async def update_user_image_links(message_from_id, path):
    """
    Функция обновляет ссылку на фотографию пользователя в
    таблице user_image_links.
    """

    connection = await connect_to_db()
    try:
        query_update_link = """
        UPDATE user_image_links 
        SET image_link=$1
        WHERE user_id=$2
        """
        await connection.execute(query_update_link, path, message_from_id)
        return True
    finally:
        await connection.close()
    return False


async def check_free_queue(request_type, db: asyncpg.pool.Pool):
    """
    Возвращает user_id всех пользователей в очереди.
    """

    async with db.acquire() as connection:
        query_select_id = """
        SELECT user_id 
        FROM queue WHERE request_type=$1 OR request_type=$2 OR request_type=$3 OR request_type=$4
        """
        user_ids = await connection.fetch(
            query_select_id,
            request_type,
            IMAGE_PAID,

            IMAGE_FOR_REFERAL,
        )

    return [user_id[0] for user_id in user_ids]


async def add_pending_image_request(
    user_id, image_tarif, db: asyncpg.pool.Pool
):
    """
    Добавляет запрос пользователя на генерацию изображений в user_images.
    """

    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)

    query_insert = """
        INSERT INTO user_images (
            user_id,
            status,
            image_tarif,
            is_generation_started, 
            date_sent
        ) VALUES ($1, $2, $3, $4, $5)
        RETURNING id
    """
    values = (
        user_id,
        PENDING,
        image_tarif,
        0,
        now_formatted,
    )

    async with db.acquire() as connection:
        async with connection.transaction():
            record = await connection.fetchrow(query_insert, *values)

    return record["id"]


async def add_history_collage_links(
    user_id, collage_type, id_in_user_images, db: asyncpg.pool.Pool
):
    """
    Добавляет строку с новым коллажом в таблицу.
    Возвращает id новоой строки.
    """

    query_insert = """
        INSERT INTO history_collage_links (
            user_id,
            user_images_id,
            collage_type
        ) VALUES ($1, $2, $3)
        RETURNING id
    """
    values = (
        user_id,
        id_in_user_images,
        collage_type,
    )

    async with db.acquire() as connection:
        async with connection.transaction():
            record = await connection.fetchrow(query_insert, *values)

    return record["id"]


async def add_to_check_user_image_queue(
    message,
    request_type,
    user_image_link,
    db: asyncpg.pool.Pool,
):
    """
    Функция добавляет задачи в таблицу check_user_image_queue
    для проверки изображения пользователя и генерации коллажей.
    """

    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    query_queue = """
        INSERT INTO check_user_image_queue (
            user_id,
            request_type,
            status,
            user_image_link,
            datetime
        ) VALUES ($1, $2, $3, $4, $5)
    """
    
    if message == types.CallbackQuery:
        values_queue = (
            message.message.chat.id,
            request_type,
            PENDING,
            user_image_link,
            now_formatted,
        )

    else:
        values_queue = (
            message.chat.id,
            request_type,
            PENDING,
            user_image_link,
            now_formatted,
        )
    
    async with db.acquire() as connection:
        async with connection.transaction():
            await connection.execute(query_queue, *values_queue)

    return True


async def add_user_image_request_to_queue(
    user_id,
    image_request_number,
    image_request_id,
    image_reference_link,
    current_user_image_link,
    total_images,
    request_type,
    db: asyncpg.pool.Pool,
    id_in_history_collage_links=None,
):
    """
    Добавляет запрос пользователя на генерацию изображений в очередь в queue
    и в history_image_links для сохранения истории.
    Одна строчка - одно изображение.
    """

    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    query_queue = """
        INSERT INTO queue (
            user_id,
            image_request_number,
            request_type,
            image_request_id,
            status,
            image_link,
            total_images,
            datetime
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    values_queue = (
        user_id,
        image_request_number,
        request_type,
        image_request_id,
        PENDING,
        image_reference_link,
        total_images,
        now_formatted,
    )
    async with db.acquire() as connection:
        async with connection.transaction():
            await connection.execute(query_queue, *values_queue)
            # await connection.execute(query_history, *values_history)

    return True


async def update_target_image_link_in_history_image_links(
    image_request_id, reference_path, target_image_link, db: asyncpg.pool.Pool
):
    """Обновляет target_image_link в таблице history_image_links."""

    query = """
        UPDATE history_image_links
        SET image_target_link = $1
        WHERE image_request_id = $2 AND image_reference_link = $3
    """

    async with db.acquire() as connection:
        await connection.execute(
            query, target_image_link, image_request_id, reference_path
        )

    return True





async def select_ready_in_check_user_image_queue():
    """
    Проверяет в базе наличие выполненных задач в check_user_image_queue
    со значением status=READY.
    """

    connection = await connect_to_db()
    try:
        query_select = """
        SELECT * FROM check_user_image_queue
        WHERE status=$1
        """
        values_select = (READY,)
        result = await connection.fetch(query_select, *values_select)

        if result:
            query_delete = """
            DELETE FROM check_user_image_queue 
            WHERE id = $1
            """
            values_delete = (result[0]["id"],)
            await connection.execute(query_delete, *values_delete)

            return result[0]
    finally:
        await connection.close()
    return False


async def select_ready_images():
    """
    Проверяет в базе наличие выполненных задач в user_images
    со значением status=READY.
    """

    query = """
        SELECT * FROM user_images 
        JOIN history_image_links
        ON user_images.id = history_image_links.image_request_id
        WHERE status=$1 AND image_tarif=$2 AND is_collage_sended=$3
    """
    query_update = """
            UPDATE user_images SET status = $1 
            WHERE id = $2
    """
    connection = await connect_to_db()
    try:
        for image_tarif in [
            IMAGE_PAID,

            IMAGE_FOR_REFERAL,
            IMAGE_COLLAGE_50,
            IMAGE_COLLAGE_100,
        ]:
            result = await connection.fetch(query, READY, image_tarif, 0)
            if result:
                if (
                    result[0]["image_tarif"] != IMAGE_COLLAGE_50
                    and result[0]["image_tarif"] != IMAGE_COLLAGE_100
                ):
                    values = (SENT, result[0]["image_request_id"])
                    await connection.execute(query_update, *values)
                return result[0]
    finally:
        await connection.close()
    return result


async def get_first_request_type_in_queue(db: asyncpg.pool.Pool):
    """Возвращает первый запрос в очереди."""

    query = """
    SELECT * FROM queue 
    JOIN user_image_links 
    ON queue.user_id = user_image_links.user_id 
    WHERE queue.request_type=$1
    AND queue.status=$2
    """

    async with db.acquire() as connection:
        for request_type in [
            IMAGE_PAID,
            IMAGE_FOR_REFERAL,
            IMAGE_COLLAGE_50,
            IMAGE_COLLAGE_100,
        ]:
            result = await connection.fetch(query, request_type, PENDING)

            if result:
                return result[-1]

    return None


async def get_all_request_type_in_queue(db: asyncpg.pool.Pool):
    """
    Возвращает все строки в очереди в соответствии с запросом.
    Для
    """

    query = """
    SELECT * FROM queue 
    JOIN user_image_links 
    ON queue.user_id = user_image_links.user_id 
    WHERE queue.request_type IN ($1, $2)
    AND queue.status=$3
    """

    async with db.acquire() as connection:
        request_types = [IMAGE_PAID]
        results = await connection.fetch(query, *request_types, PENDING)

    return results


async def change_in_queue_image_request_status_to_drawing(
    image_request_id, db: asyncpg.pool.Pool
):
    """Обновляет в queue status запроса на генерацию."""

    async with db.acquire() as connection:
        async with connection.transaction():
            query = """
            UPDATE queue SET status = $1 
            WHERE id = $2 AND status = $3
            """
            values = (DRAWING, image_request_id, PENDING)
            await connection.execute(query, *values)


async def remove_requests_from_queue(
    request_type, image_request_id, image_request_number, db: asyncpg.pool.Pool
):
    """
    Удаляет строки в queue c request_type и image_request_id и
    возвращает ссылки на готовые изображения
    (для image_free=5, для image_paid=10)
    """

    async with db.acquire() as connection:
        async with connection.transaction():
            query_select = """
            SELECT image_target_link FROM history_image_links
            WHERE image_request_id=$1
            AND image_request_number <= $2
            AND image_request_number > ($2 - 10)
            """
            values_select = (image_request_id, image_request_number)
            result = await connection.fetch(query_select, *values_select)

            query_delete = """
            DELETE FROM queue 
            WHERE request_type = $1 
            AND image_request_id = $2 
            AND image_request_number <= $3
            """
            values_delete = (
                request_type,
                image_request_id,
                image_request_number,
            )
            await connection.execute(query_delete, *values_delete)

            return result


async def change_user_images_status_sent(
    user_image_id, status, db: asyncpg.pool.Pool
):
    """Обновляет status в sent в user_images по id."""

    async with db.acquire() as connection:
        async with connection.transaction():
            query_update = """
                UPDATE user_images SET status = $1 
                WHERE id = $2
            """
            values = (status, user_image_id)
            await connection.execute(query_update, *values)


# async def conn_change_user_images_status_sent(user_image_id, status):
#     """Обновляет status в sent в user_images по id."""

#     connection = await connect_to_db()
#     try:
#         query_update = """
#             UPDATE user_images SET status = $1
#             WHERE id = $2
#         """
#         values = (status, user_image_id)
#         await connection.execute(query_update, *values)
#     finally:
#         await connection.close()


async def change_collage_status_sent(user_image_id):
    """Обнавляет is_collage_sended в 1 в user_images по id."""

    connection = await connect_to_db()
    try:
        query_update = """
            UPDATE user_images SET is_collage_sended = $1 
            WHERE id = $2
        """
        values = (1, user_image_id)
        await connection.execute(query_update, *values)
    finally:
        await connection.close()


async def set_checker(id, db: asyncpg.pool.Pool):
    """Изменяет checker для регулирования работы планировщика."""

    async with db.acquire() as connection:
        await connection.execute(
            """
                UPDATE checker SET checker = $1
                WHERE checker = $2""",
            (id, 0 if id == 1 else 1),
        )


async def check_referal_exists(args, new_user_id, db: asyncpg.pool.Pool):
    """
    Проверяет реферальный код, и если находит в таблице user или referal_table,
    возвращает этот код, иначе возвращает None.
    Также добавлят данные в таблицу referals.
    Также возвращает user_id реферера чтобы отправить ему бонус.
    """

    if args == "":
        return None, None, None

    async with db.acquire() as connection:
        result_ref = await connection.fetchrow(
            """SELECT * FROM users
            WHERE ref_code=$1
            """,
            args,
        )
        referal_table_ref = await connection.fetchrow(
            """SELECT * FROM referal_table
            WHERE referal_code=$1
            """,
            args,
        )
        if not result_ref and not referal_table_ref:
            return None, None, None

        result = await connection.fetchrow(
            """SELECT * FROM users
            WHERE user_id=$1
            """,
            new_user_id,
        )
        if result:
            return None, None, None
        send_ref = True
        if referal_table_ref:
            send_ref = False
        result_ref = (
            result_ref["user_id"]
            if result_ref
            else referal_table_ref["referal_code"]
        )

    return args, result_ref, send_ref
