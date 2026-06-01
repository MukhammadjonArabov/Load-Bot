import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from yuklabot.config import config
from yuklabot.database.db import add_download
from yuklabot.keyboards.inline import quality_keyboard
from yuklabot.locales import get_text
from yuklabot.utils.cleaner import delete_file
from yuklabot.utils.downloader import download_video, get_video_info
from yuklabot.utils.helpers import extract_url, format_duration, truncate_title
from yuklabot.utils.url_cache import url_cache


router = Router()


@router.message(F.text.func(lambda text: bool(text and ("youtube.com" in text.lower() or "youtu.be" in text.lower()))))
async def youtube_url(message: Message, db_user) -> None:
    url = extract_url(message.text)
    if not url:
        await message.answer(get_text(db_user.language, "invalid_link"))
        return

    status = await message.answer(get_text(db_user.language, "fetching_info"))
    info = await get_video_info(url)
    if not info["success"]:
        await status.edit_text(get_text(db_user.language, "download_error"))
        return

    text = (
        f"▶️ <b>{truncate_title(info['title'], 80)}</b>\n"
        f"👤 {info.get('uploader') or '-'}\n"
        f"⏱ {format_duration(info.get('duration'))}\n\n"
        f"{get_text(db_user.language, 'choose_quality')}"
    )
    await status.edit_text(text, reply_markup=quality_keyboard("youtube", url))


@router.callback_query(F.data.startswith("dl:youtube:"))
async def youtube_download(callback: CallbackQuery, db_user) -> None:
    await callback.answer()
    await _handle_download(callback, db_user)


@router.message(Command("youtube"))
async def youtube_command(message: Message, db_user) -> None:
    await message.answer(get_text(db_user.language, "send_link"))


async def _handle_download(callback: CallbackQuery, db_user) -> None:
    _, platform, quality, url_hash = callback.data.split(":", 3)
    url = url_cache.get(url_hash)
    if not url:
        await callback.message.edit_text(get_text(db_user.language, "invalid_link"))
        return

    await callback.message.edit_text(get_text(db_user.language, "downloading"))
    result = await download_video(url, quality)
    if not result["success"]:
        await callback.message.edit_text(get_text(db_user.language, "download_error"))
        return

    file_size = result["file_size"]
    if file_size > config.MAX_FILE_SIZE:
        asyncio.create_task(delete_file(result["file_path"]))
        await callback.message.edit_text(get_text(db_user.language, "file_too_large", size=file_size))
        return

    file_path = result["file_path"]
    file_type = "audio" if quality == "mp3" else "video"
    await _send_file(callback.message, file_path, file_type, result["title"])
    await add_download(db_user.id, platform, url, result["title"], file_type, quality, file_size)
    asyncio.create_task(delete_file(file_path))
    await callback.message.edit_text(get_text(db_user.language, "download_success", size=file_size))


async def _send_file(message: Message, file_path: str, file_type: str, title: str) -> None:
    file = FSInputFile(file_path, filename=file_path.split("\\")[-1].split("/")[-1])
    caption = truncate_title(title, 900)
    if file_type == "audio":
        await message.answer_audio(file, caption=caption)
    else:
        try:
            await message.answer_video(file, caption=caption)
        except Exception:
            await message.answer_document(file, caption=caption)
