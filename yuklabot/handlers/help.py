from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from locales import get_text


router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "help"))


@router.message(F.text.regexp(r"https?://"))
async def unsupported_url(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "invalid_link"))
