import asyncio
import os
import re
import uuid
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError

from yuklabot.config import config

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


async def download_video(url: str, quality: str, output_dir: str = "downloads") -> dict:
    Path(output_dir).mkdir(exist_ok=True)
    quality = _normalize_quality(quality)
    output_id = str(uuid.uuid4())
    is_instagram = "instagram.com" in url.lower()

    format_map = {
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "mp3": "bestaudio/best",
        "video": "bestvideo+bestaudio/best[ext=mp4]/best",
        "image": "best",  # Instagram image — alohida handle qilinadi
    }

    ydl_opts = {
        "format": format_map.get(quality, "best"),
        "outtmpl": str(Path(output_dir) / f"{output_id}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "noplaylist": True,
        "overwrites": True,
        "socket_timeout": 30,
        "retries": 3,
        # Instagram uchun: rasm yuklab olish
        "write_all_thumbnails": False,
    }

    # Instagram rasmini alohida handle qil
    if is_instagram and quality == "image":
        ydl_opts["skip_download"] = False
        ydl_opts["format"] = "best"
        # Instagram post rasm bo'lsa thumbnail sifatida chiqadi
        # shuning uchun writethumbnail yoqamiz
        ydl_opts["writethumbnail"] = True
        ydl_opts["skip_download"] = True
        ydl_opts["outtmpl"] = str(Path(output_dir) / f"{output_id}.%(ext)s")

    if quality == "mp3":
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _download_sync(url, ydl_opts, quality, is_instagram))


def _download_sync(url: str, ydl_opts: dict, quality: str, is_instagram: bool = False) -> dict:
    try:
        return _run_download(url, ydl_opts, quality, is_instagram)
    except DownloadError as exc:
        err_str = str(exc)
        if "Requested format is not available" not in err_str:
            return {"success": False, "error": _friendly_error(err_str)}
        fallback_opts = dict(ydl_opts)
        fallback_opts["format"] = "bestaudio/best" if quality == "mp3" else "best"
        try:
            return _run_download(url, fallback_opts, quality, is_instagram)
        except Exception as fallback_exc:
            return {"success": False, "error": _friendly_error(str(fallback_exc))}
    except Exception as exc:
        return {"success": False, "error": _friendly_error(str(exc))}


def _run_download(url: str, ydl_opts: dict, quality: str, is_instagram: bool = False) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        # Instagram rasm: thumbnail fayl
        if is_instagram and quality == "image":
            output_dir = Path(ydl_opts["outtmpl"]).parent
            # thumbnail fayllarini qidirish
            thumbnails = list(output_dir.glob("*.jpg")) + list(output_dir.glob("*.webp")) + list(output_dir.glob("*.png"))
            # eng yangi faylni olish
            if thumbnails:
                thumb = max(thumbnails, key=lambda p: p.stat().st_mtime)
                file_size = thumb.stat().st_size / (1024 * 1024)
                return {
                    "success": True,
                    "file_path": str(thumb),
                    "title": info.get("title", "Instagram"),
                    "file_size": round(file_size, 2),
                    "duration": 0,
                    "platform": "instagram",
                    "file_type": "photo",
                }
            # Thumbnail topilmasa video sifatida yukla
            fallback_opts = dict(ydl_opts)
            fallback_opts.pop("writethumbnail", None)
            fallback_opts.pop("skip_download", None)
            fallback_opts["format"] = "best"
            with yt_dlp.YoutubeDL(fallback_opts) as ydl2:
                info2 = ydl2.extract_info(url, download=True)
                if "entries" in info2 and info2["entries"]:
                    info2 = info2["entries"][0]
                filename = ydl2.prepare_filename(info2)
                if not os.path.exists(filename):
                    filename = _find_downloaded_file(filename)
                file_size = os.path.getsize(filename) / (1024 * 1024)
                return {
                    "success": True,
                    "file_path": filename,
                    "title": info2.get("title", "Instagram"),
                    "file_size": round(file_size, 2),
                    "duration": info2.get("duration", 0) or 0,
                    "platform": "instagram",
                    "file_type": "video",
                }

        filename = ydl.prepare_filename(info)
        if quality == "mp3":
            filename = str(Path(filename).with_suffix(".mp3"))
        elif not os.path.exists(filename):
            filename = _find_downloaded_file(filename)

        if not filename or not os.path.exists(filename):
            return {"success": False, "error": "Fayl topilmadi. Qaytadan urinib ko'ring."}

        file_size = os.path.getsize(filename) / (1024 * 1024)
        return {
            "success": True,
            "file_path": filename,
            "title": info.get("title", "Video"),
            "file_size": round(file_size, 2),
            "duration": info.get("duration", 0) or 0,
            "platform": detect_platform(url) or info.get("extractor", "unknown"),
            "file_type": "video",
        }


async def get_video_info(url: str) -> dict:
    """Faqat meta ma'lumot olish — download qilmasdan."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 15,
    }
    loop = asyncio.get_running_loop()

    def _get_info() -> dict:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                return {
                    "success": True,
                    "title": info.get("title", "Video"),
                    "duration": info.get("duration", 0) or 0,
                    "platform": detect_platform(url) or info.get("extractor", "unknown"),
                    "thumbnail": info.get("thumbnail"),
                    "uploader": info.get("uploader", ""),
                }
        except Exception as exc:
            return {"success": False, "error": _friendly_error(str(exc))}

    return await loop.run_in_executor(None, _get_info)


def detect_platform(url: str) -> str:
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "instagram.com" in url:
        return "instagram"
    if "tiktok.com" in url:
        return "tiktok"
    if "twitter.com" in url or "x.com" in url:
        return "twitter"
    return "unknown"


def _normalize_quality(quality: str) -> str:
    if quality.endswith("p"):
        return quality[:-1]
    return quality


def _find_downloaded_file(prepared_filename: str) -> str | None:
    base_path = Path(prepared_filename)
    directory = base_path.parent
    stem = re.escape(base_path.stem)
    candidates = sorted(
        directory.glob(f"{base_path.stem}.*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        if candidate.is_file() and re.match(rf"^{stem}\.", candidate.name):
            return str(candidate)
    return None


def _friendly_error(error: str) -> str:
    """Foydalanuvchiga qulay xato xabari."""
    err = error.lower()
    if "private" in err or "login" in err or "authentication" in err:
        return "Bu kontent shaxsiy yoki login talab qiladi."
    if "not available" in err or "unavailable" in err:
        return "Bu kontent mavjud emas yoki o'chirilgan."
    if "copyright" in err:
        return "Bu kontent mualliflik huquqi bilan himoyalangan."
    if "timeout" in err or "timed out" in err:
        return "Server javob bermadi. Qaytadan urinib ko'ring."
    if "rate" in err or "too many" in err:
        return "Juda ko'p so'rov. Bir oz kuting."
    if "network" in err or "connection" in err:
        return "Internet ulanish xatosi. Qaytadan urinib ko'ring."
    return "Yuklab bo'lmadi. Linkni tekshiring yoki keyinroq urinib ko'ring."