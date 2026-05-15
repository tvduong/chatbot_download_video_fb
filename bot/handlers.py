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
from bot.trash_talk import (
    is_trash_talk,
    random_comeback,
    random_roast,
    reply_to_insult,
)

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "Gửi link cho anh đi mấy con vợ.\n\n"
    "Ví dụ:\n"
    "• https://www.facebook.com/watch/?v=...\n"
    "• https://fb.watch/xxxxx/\n"
    "• https://www.facebook.com/reel/...\n\n"
    "Lệnh:\n"
    "/start — hướng dẫn\n"
    "/chui — bố chửi random\n"
    "/cai — chửi lộn với bot (gửi tin nhắn sau lệnh)"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def chui_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(random_roast())


async def cai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = True
    await update.message.reply_text(
        "Ok, cãi đi. Gửi tin nhắn tiếp theo, bố đáp.\n"
        "Gửi /stop để tắt chế độ cãi."
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = False
    await update.message.reply_text("Thôi, bố nghỉ miệng. Gửi link FB đi.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if is_facebook_url(text):
        await _handle_facebook_link(update, text)
        return

    if context.user_data.get("cai_mode") or is_trash_talk(text):
        await update.message.reply_text(
            reply_to_insult() if is_trash_talk(text) else random_comeback()
        )
        return

    if text.lower() in {"chui", "chửi", "cãi", "cai", "đánh nhau", "danh nhau"}:
        await update.message.reply_text(random_comeback())
        return

    await update.message.reply_text(
        f"{random_roast()}\n\n"
        "Gửi link Facebook hoặc /chui — bố chửi cho vui."
    )


async def _handle_facebook_link(update: Update, text: str) -> None:
    url = extract_facebook_url(text)
    if not url:
        return

    status = await update.message.reply_text("Bố đang tải, đợi điđi...")
    await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    filepath = None
    try:
        filepath = download_facebook_video(url)
        await status.edit_text("Bố đang gửi...")

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
