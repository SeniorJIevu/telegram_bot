import logging

import aiolimiter
from aiogram.dispatcher.middlewares import BaseMiddleware

limiter = aiolimiter.AsyncLimiter(26, 1)


class RateLimitMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        async with limiter:
            await limiter.acquire(1)
            logging.info(
                f'{message["from"]["id"]} {message["from"]["first_name"]} {message["from"]["last_name"]} {message["from"]["username"]} {message["date"]} {message["text"]} '
            )
