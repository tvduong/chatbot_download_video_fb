import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
def _clean_token(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


TELEGRAM_BOT_TOKEN = _clean_token(os.getenv("TELEGRAM_BOT_TOKEN", ""))
_default_download = "/tmp/downloads" if os.getenv("RENDER") or os.getenv("FLY_APP_NAME") or os.getenv("KOYEB_APP_NAME") else BASE_DIR / "downloads"
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", _default_download))
MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "48"))
FB_COOKIES = os.getenv("FB_COOKIES")

FB_URL_PATTERN = (
    r"(https?://)?(www\.|m\.|web\.)?"
    r"(facebook\.com|fb\.watch|fb\.com)/\S+"
)
