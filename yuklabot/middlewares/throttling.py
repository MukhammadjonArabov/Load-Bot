import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from yuklabot.locales import get_text


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 3, window: int = 10) -> None:
        self.limit = limit
        self.window = window
        self.requests: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        user_requests = self.requests[user_id]

        while user_requests and now - user_requests[0] > self.window:
            user_requests.popleft()

        if len(user_requests) >= self.limit:
            user = data.get("db_user")
            lang = getattr(user, "language", "uz")
            await event.answer(get_text(lang, "rate_limited"))
            return None

        user_requests.append(now)
        return await handler(event, data)
