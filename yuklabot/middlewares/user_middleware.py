from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from yuklabot.database.db import get_or_create_user
from yuklabot.locales import get_text


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = None
        answer_target = None

        if isinstance(event, Message):
            telegram_user = event.from_user
            answer_target = event
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
            answer_target = event.message

        if not telegram_user:
            return await handler(event, data)

        full_name = telegram_user.full_name or telegram_user.first_name or str(telegram_user.id)
        user = await get_or_create_user(telegram_user.id, telegram_user.username, full_name)
        data["db_user"] = user

        if user.is_banned:
            if answer_target:
                await answer_target.answer(get_text(user.language, "banned"))
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        return await handler(event, data)
