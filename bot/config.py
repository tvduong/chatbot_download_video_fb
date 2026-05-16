import os

from dotenv import load_dotenv

load_dotenv()


def _clean_token(raw: str) -> str:
    return raw.strip().strip('"').strip("'")


TELEGRAM_BOT_TOKEN = _clean_token(os.getenv("TELEGRAM_BOT_TOKEN", ""))
