from yuklabot.locales.en import MESSAGES as EN_MESSAGES
from yuklabot.locales.ru import MESSAGES as RU_MESSAGES
from yuklabot.locales.uz import MESSAGES as UZ_MESSAGES


LOCALES = {
    "uz": UZ_MESSAGES,
    "ru": RU_MESSAGES,
    "en": EN_MESSAGES,
}


def get_text(language: str | None, key: str, **kwargs: object) -> str:
    messages = LOCALES.get(language or "uz", UZ_MESSAGES)
    template = messages.get(key, UZ_MESSAGES.get(key, key))
    return template.format(**kwargs)
