from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from yuklabot.utils.url_cache import url_cache


def quality_keyboard(platform: str, url: str) -> InlineKeyboardMarkup:
    url_hash = url_cache.put(url)
    builder = InlineKeyboardBuilder()

    if platform == "youtube":
        buttons = [
            ("📹 Video", "video"),
            ("🎵 MP3", "mp3"),
        ]
    else:
        buttons = [
            ("📹 Video", "video"),
            ("🖼 Rasm", "image"),
        ]

    for text, quality in buttons:
        builder.button(text=text, callback_data=f"dl:{platform}:{quality}:{url_hash}")
    builder.adjust(2)
    return builder.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def history_keyboard(downloads: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for download in downloads[:5]:
        title = download.title if len(download.title) <= 32 else f"{download.title[:29]}..."
        builder.button(text=f"{download.platform}: {title}", callback_data=f"hist:{download.id}")
    builder.adjust(1)
    return builder.as_markup()
