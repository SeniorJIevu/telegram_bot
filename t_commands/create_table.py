import asyncpg

from constants import env


async def create_table():
    """Create table if not exists."""

    async with asyncpg.create_pool(
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
        database=env["DB_NAME"],
        host=env["DB_HOST"],
    ) as db:
        async with db.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                        CREATE TABLE IF NOT EXISTS "users" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT  NOT NULL UNIQUE,
                            referrer_id TEXT DEFAULT NULL,
                            last_login TEXT,
                            username TEXT,
                            first_name TEXT,
                            last_name TEXT,
                            gender TEXT,
                            last_msg TEXT,
                            join_date TEXT,
                            user_images BIGINT  DEFAULT 0,
                            ref_code TEXT DEFAULT NULL
                        );

                        CREATE TABLE IF NOT EXISTS "user_images" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            status TEXT,
                            image_tarif TEXT,
                            is_generation_started BIGINT ,
                            is_collage_sended BIGINT  DEFAULT 0,
                            date_sent TEXT,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id)
                        );

                        CREATE TABLE IF NOT EXISTS "user_image_links" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT  NOT NULL,
                            image_link TEXT,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id)
                        );

                        CREATE TABLE IF NOT EXISTS "history_collage_links" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT  NOT NULL,
                            user_images_id BIGINT  NOT NULL,
                            collage_type TEXT DEFAULT NULL,
                            image_collage_link TEXT DEFAULT NULL,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id),
                            FOREIGN KEY(user_images_id) REFERENCES "user_images" (id)
                        );

                        CREATE TABLE IF NOT EXISTS "history_image_links" (
                            id SERIAL PRIMARY KEY,
                            image_request_id BIGINT ,
                            user_id BIGINT  NOT NULL,
                            image_request_number BIGINT  NOT NULL,
                            user_image_link TEXT,
                            image_reference_link TEXT,
                            image_target_link TEXT DEFAULT NULL,
                            collage_link_id BIGINT  DEFAULT NULL,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id),
                            FOREIGN KEY(collage_link_id) REFERENCES "history_collage_links" (id)
                        );

                        CREATE TABLE IF NOT EXISTS "queue" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT  NOT NULL,
                            request_type TEXT,
                            image_request_number BIGINT ,
                            image_request_id BIGINT ,
                            status TEXT,
                            image_link TEXT,
                            total_images BIGINT,
                            datetime TEXT DEFAULT NULL,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id),
                            FOREIGN KEY(image_request_id) REFERENCES "user_images" (id)
                        );

                        CREATE TABLE IF NOT EXISTS "check_user_image_queue" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            request_type TEXT,
                            status TEXT,
                            user_image_link TEXT,
                            datetime TEXT DEFAULT NULL,
                            check_analyse_face INT DEFAULT 0,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id)
                        );

                        CREATE TABLE IF NOT EXISTS "referal_table" (
                            id SERIAL PRIMARY KEY,
                            referal_code TEXT
                        );

                        CREATE TABLE IF NOT EXISTS "payment_table" (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            referal_code TEXT,
                            amount BIGINT,
                            image_tarif TEXT,
                            datetime TEXT DEFAULT NULL,
                            FOREIGN KEY(user_id) REFERENCES "users" (user_id)
                        );
                    """
                )
