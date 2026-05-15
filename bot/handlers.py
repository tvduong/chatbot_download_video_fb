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
from bot.trash_talk import generate_reply_with_streak, is_trash_talk

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
    uid = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(
        generate_reply_with_streak("", uid, 0, is_command_chui=True)
    )


async def cai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = True
    context.user_data["cai_streak"] = 0
    uid = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(
        generate_reply_with_streak("cãi đi", uid, 1, cai_mode=True)
        + "\n\nGửi tin tiếp — /stop để nghỉ."
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = False
    context.user_data["cai_streak"] = 0
    await update.message.reply_text("Thôi, bố nghỉ. Có clip thì quăng link.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if is_facebook_url(text):
        await _handle_facebook_link(update, text)
        return

    uid = update.effective_user.id if update.effective_user else 0
    cai_mode = context.user_data.get("cai_mode", False)

    if cai_mode or is_trash_talk(text) or text.lower() in {
        "chui", "chửi", "cãi", "cai", "đánh nhau", "danh nhau"
    }:
        streak = context.user_data.get("cai_streak", 0) + 1
        context.user_data["cai_streak"] = streak
        await update.message.reply_text(
            generate_reply_with_streak(text, uid, streak, cai_mode=cai_mode or True)
        )
        return

    await update.message.reply_text(
        generate_reply_with_streak(text, uid, 0, cai_mode=False)
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
