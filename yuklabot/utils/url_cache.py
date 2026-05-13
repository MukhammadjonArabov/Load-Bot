import time
from hashlib import sha256


class UrlCache:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[str, float]] = {}

    def put(self, url: str) -> str:
        key = sha256(f"{url}:{time.monotonic()}".encode("utf-8")).hexdigest()[:16]
        self._items[key] = (url, time.monotonic() + self.ttl_seconds)
        self.cleanup()
        return key

    def get(self, key: str) -> str | None:
        item = self._items.get(key)
        if not item:
            return None
        url, expires_at = item
        if expires_at < time.monotonic():
            self._items.pop(key, None)
            return None
        return url

    def cleanup(self) -> None:
        now = time.monotonic()
        expired = [key for key, (_, expires_at) in self._items.items() if expires_at < now]
        for key in expired:
            self._items.pop(key, None)


url_cache = UrlCache()
