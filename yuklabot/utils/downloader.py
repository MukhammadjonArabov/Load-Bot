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
    """
    Downloads video/audio from URL.
    quality options: '360', '720', '1080', 'mp3', 'video', 'image'
    Returns: success, file_path, title, file_size in MB, duration, platform.
    """
    Path(output_dir).mkdir(exist_ok=True)
    quality = _normalize_quality(quality)
    output_id = str(uuid.uuid4())

    format_map = {
        "360": "best[height<=360]/best",
        "720": "best[height<=720]/best",
        "1080": "best[height<=1080]/best",
        "mp3": "bestaudio/best",
        "video": "best[ext=mp4]/best",
        "image": "best",
    }

    ydl_opts = {
        "format": format_map.get(quality, "best"),
        "outtmpl": str(Path(output_dir) / f"{output_id}.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "noplaylist": True,
        "max_filesize": config.max_file_size_bytes,
        "overwrites": True,
    }

    if quality == "mp3":
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _download_sync(url, ydl_opts, quality))


def _download_sync(url: str, ydl_opts: dict, quality: str) -> dict:
    try:
        return _run_download(url, ydl_opts, quality)
    except DownloadError as exc:
        if "Requested format is not available" not in str(exc):
            return {"success": False, "error": str(exc)}
        fallback_opts = dict(ydl_opts)
        fallback_opts["format"] = "bestaudio/best" if quality == "mp3" else "best"
        try:
            return _run_download(url, fallback_opts, quality)
        except Exception as fallback_exc:
            return {"success": False, "error": str(fallback_exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _run_download(url: str, ydl_opts: dict, quality: str) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)
        if quality == "mp3":
            filename = str(Path(filename).with_suffix(".mp3"))
        elif not os.path.exists(filename):
            filename = _find_downloaded_file(filename)

        if not filename or not os.path.exists(filename):
            return {"success": False, "error": "Downloaded file was not found."}

        file_size = os.path.getsize(filename) / (1024 * 1024)
        return {
            "success": True,
            "file_path": filename,
            "title": info.get("title", "Video"),
            "file_size": round(file_size, 2),
            "duration": info.get("duration", 0) or 0,
            "platform": detect_platform(url) or info.get("extractor", "unknown"),
        }


async def get_video_info(url: str) -> dict:
    ydl_opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
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
            return {"success": False, "error": str(exc)}

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
    candidates = sorted(directory.glob(f"{base_path.stem}.*"), key=lambda path: path.stat().st_mtime, reverse=True)
    for candidate in candidates:
        if candidate.is_file() and re.match(rf"^{stem}\.", candidate.name):
            return str(candidate)
    return None
