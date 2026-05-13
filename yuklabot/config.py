import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_admin_ids() -> list[int]:
    raw_ids = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "")
    admin_ids: list[int] = []
    for raw_id in raw_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id.isdigit():
            admin_ids.append(int(raw_id))
    return admin_ids


@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    ADMIN_IDS: list[int]
    MAX_FILE_SIZE: int

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE * 1024 * 1024


config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
    DB_HOST=os.getenv("DB_HOST", "localhost"),
    DB_PORT=_get_int("DB_PORT", 5432),
    DB_NAME=os.getenv("DB_NAME", "yuklabot_db"),
    DB_USER=os.getenv("DB_USER", "postgres"),
    DB_PASSWORD=os.getenv("DB_PASSWORD", ""),
    ADMIN_IDS=_get_admin_ids(),
    MAX_FILE_SIZE=_get_int("MAX_FILE_SIZE", 50),
)
