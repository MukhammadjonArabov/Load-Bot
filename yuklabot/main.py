import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from yuklabot.config import config
from yuklabot.database.db import init_db
from yuklabot.handlers import admin, help, instagram, start, tiktok, twitter, youtube
from yuklabot.middlewares.throttling import ThrottlingMiddleware
from yuklabot.middlewares.user_middleware import UserMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Fill .env before starting the bot.")

    await init_db()
    logger.info("Database initialized")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(youtube.router)
    dp.include_router(instagram.router)
    dp.include_router(tiktok.router)
    dp.include_router(twitter.router)
    dp.include_router(help.router)

    try:
        await bot.set_my_name("YuklaBot")
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Start YuklaBot"),
                BotCommand(command="help", description="Help"),
            ]
        )
    except Exception as exc:
        logger.warning("Could not update bot profile metadata: %s", exc)

    logger.info("Bot started!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
