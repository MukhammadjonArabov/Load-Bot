import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from database.db import get_download_by_id, get_user_downloads, update_user_language
from keyboards.inline import history_keyboard, language_keyboard
from keyboards.reply import main_menu
from locales import get_text


router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, db_user) -> None:
    if db_user.downloads_count == 0:
        logger.info("New user: %s %s", db_user.id, db_user.username)
    await message.answer(
        get_text(db_user.language, "welcome", name=message.from_user.full_name),
        reply_markup=main_menu(db_user.language),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, db_user) -> None:
    language = callback.data.split(":", 1)[1]
    await update_user_language(db_user.id, language)
    await callback.message.edit_text(get_text(language, "language_changed"))
    await callback.message.answer(get_text(language, "send_link"), reply_markup=main_menu(language))
    await callback.answer()


@router.message(F.text.in_({"📋 Tarix", "📋 История", "📋 History"}))
async def show_history(message: Message, db_user) -> None:
    downloads = await get_user_downloads(db_user.id, limit=20)
    if not downloads:
        await message.answer(get_text(db_user.language, "history_empty"))
        return

    lines = [get_text(db_user.language, "history")]
    for item in downloads:
        lines.append(
            f"{item.id}. <b>{item.platform.title()}</b> | {item.quality} | "
            f"{item.file_size:.2f} MB\n{item.title}"
        )
    await message.answer("\n\n".join(lines), reply_markup=history_keyboard(downloads))


@router.message(F.text.in_({"⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"}))
async def show_settings(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "choose_language"), reply_markup=language_keyboard())


@router.message(F.text.in_({"📥 Yuklab olish", "📥 Скачать", "📥 Download"}))
async def ask_link(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "send_link"))


@router.message(F.text.in_({"❓ Yordam", "❓ Помощь", "❓ Help"}))
async def menu_help(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "help"))


@router.callback_query(F.data.startswith("hist:"))
async def history_item(callback: CallbackQuery, db_user) -> None:
    download_id = int(callback.data.split(":", 1)[1])
    item = await get_download_by_id(download_id, db_user.id)
    if not item:
        await callback.answer()
        return
    await callback.message.answer(
        f"📋 <b>{item.title}</b>\n\n"
        f"Platform: {item.platform}\n"
        f"Type: {item.file_type}\n"
        f"Quality: {item.quality}\n"
        f"Size: {item.file_size:.2f} MB\n"
        f"URL: {item.url}"
    )
    await callback.answer()
