import re
from pathlib import Path

import yt_dlp

from bot.config import DOWNLOAD_DIR, FB_COOKIES, FB_URL_PATTERN, MAX_FILE_SIZE_MB

FB_RE = re.compile(FB_URL_PATTERN, re.IGNORECASE)
MAX_BYTES = int(MAX_FILE_SIZE_MB * 1024 * 1024)


class DownloadError(Exception):
    pass


def is_facebook_url(text: str) -> bool:
    return bool(FB_RE.search(text.strip()))


def extract_facebook_url(text: str) -> str | None:
    match = FB_RE.search(text.strip())
    return match.group(0) if match else None


def _ydl_opts(out_dir: Path) -> dict:
    opts: dict = {
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
    }
    if FB_COOKIES and Path(FB_COOKIES).is_file():
        opts["cookiefile"] = FB_COOKIES
    return opts


def download_facebook_video(url: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with yt_dlp.YoutubeDL(_ydl_opts(DOWNLOAD_DIR)) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise DownloadError("Không lấy được thông tin video.")

        filepath = Path(ydl.prepare_filename(info))
        if not filepath.exists():
            # Một số format đổi ext sau khi merge
            candidates = list(DOWNLOAD_DIR.glob(f"{info.get('id', '*')}.*"))
            if candidates:
                filepath = max(candidates, key=lambda p: p.stat().st_mtime)
            else:
                raise DownloadError("Tải xong nhưng không tìm thấy file.")

    size = filepath.stat().st_size
    if size > MAX_BYTES:
        filepath.unlink(missing_ok=True)
        raise DownloadError(
            f"Video quá lớn ({size / 1024 / 1024:.1f} MB). "
            f"Giới hạn bot: {MAX_FILE_SIZE_MB:.0f} MB."
        )

    return filepath
