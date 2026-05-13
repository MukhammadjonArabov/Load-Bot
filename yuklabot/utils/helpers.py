import re
from urllib.parse import urlparse


SUPPORTED_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
)


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


def format_size(bytes_value: int | float | None) -> str:
    if not bytes_value:
        return "0 MB"
    mb = float(bytes_value) / (1024 * 1024)
    return f"{mb:.1f} MB"


def is_valid_url(text: str | None) -> bool:
    if not text:
        return False
    match = re.search(r"https?://\S+", text.strip())
    if not match:
        return False
    parsed = urlparse(match.group(0))
    hostname = (parsed.hostname or "").lower()
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in SUPPORTED_DOMAINS)


def extract_url(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"https?://\S+", text.strip())
    return match.group(0).rstrip(").,]") if match else None


def truncate_title(title: str | None, max_len: int = 50) -> str:
    if not title:
        return "Video"
    title = " ".join(title.split())
    if len(title) <= max_len:
        return title
    return title[: max_len - 3].rstrip() + "..."
