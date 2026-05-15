import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.downloader import (
    DownloadError,
    download_facebook_video,
    extract_facebook_url,
    is_facebook_url,
)

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "Chào bạn! Gửi link video Facebook để tải.\n\n"
    "Ví dụ:\n"
    "• https://www.facebook.com/watch/?v=...\n"
    "• https://fb.watch/xxxxx/\n"
    "• https://www.facebook.com/reel/...\n\n"
    "Lệnh: /start — hướng dẫn"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not is_facebook_url(text):
        await update.message.reply_text(
            "Gửi link Facebook hợp lệ (facebook.com, fb.watch, fb.com)."
        )
        return

    url = extract_facebook_url(text)
    if not url:
        return

    status = await update.message.reply_text("Đang tải video, vui lòng đợi...")
    await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    filepath = None
    try:
        filepath = download_facebook_video(url)
        await status.edit_text("Đang gửi video...")

        with filepath.open("rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                supports_streaming=True,
            )
        await status.delete()
    except DownloadError as exc:
        logger.warning("Download failed: %s", exc)
        await status.edit_text(f"Không tải được: {exc}")
    except Exception:
        logger.exception("Unexpected error for url=%s", url)
        await status.edit_text("Lỗi không xác định. Thử lại sau.")
    finally:
        if filepath and filepath.exists():
            filepath.unlink(missing_ok=True)
