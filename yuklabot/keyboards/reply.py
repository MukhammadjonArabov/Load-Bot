from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


MENU_TEXTS = {
    "uz": ["📥 Yuklab olish", "📋 Tarix", "⚙️ Sozlamalar", "❓ Yordam"],
    "ru": ["📥 Скачать", "📋 История", "⚙️ Настройки", "❓ Помощь"],
    "en": ["📥 Download", "📋 History", "⚙️ Settings", "❓ Help"],
}


def main_menu(lang: str | None = "uz") -> ReplyKeyboardMarkup:
    texts = MENU_TEXTS.get(lang or "uz", MENU_TEXTS["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts[0])],
            [KeyboardButton(text=texts[1]), KeyboardButton(text=texts[2])],
            [KeyboardButton(text=texts[3])],
        ],
        resize_keyboard=True,
        input_field_placeholder=texts[0],
    )
