import logging
import random

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.downloader import (
    DownloadError,
    download_facebook_video,
    extract_facebook_url,
    is_facebook_url,
)
from bot.riddles import session as _riddles
from bot.riddles import should_ask_riddle
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
    "/cai — chửi lộn + câu đố (sai thì ăn chửi)\n"
    "/do — ra câu đố ngay\n"
    "/stop — nghỉ"
)


def _clear_riddle(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("active_riddle", None)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def chui_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else 0
    await update.message.reply_text(
        generate_reply_with_streak("", uid, 0, is_command_chui=True)
    )


async def do_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else 0
    riddle = _riddles.pick(uid)
    context.user_data["active_riddle"] = riddle
    context.user_data["cai_mode"] = True
    await update.message.reply_text(_riddles.format_question(riddle))


async def cai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = True
    context.user_data["cai_streak"] = 0
    _clear_riddle(context)
    uid = update.effective_user.id if update.effective_user else 0
    riddle = _riddles.pick(uid)
    context.user_data["active_riddle"] = riddle
    await update.message.reply_text(
        generate_reply_with_streak("cãi đi", uid, 1, cai_mode=True)
        + "\n\n"
        + _riddles.format_question(riddle)
        + "\n\n/stop để nghỉ."
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cai_mode"] = False
    context.user_data["cai_streak"] = 0
    _clear_riddle(context)
    await update.message.reply_text("Thôi, bố nghỉ. Có clip thì quăng link.")


async def _send_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int) -> None:
    riddle = _riddles.pick(uid)
    context.user_data["active_riddle"] = riddle
    await update.message.reply_text(_riddles.format_question(riddle))


async def _handle_riddle_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, uid: int
) -> bool:
    riddle = context.user_data.get("active_riddle")
    if not riddle:
        return False

    result = _riddles.check(text, riddle)

    if result == "correct":
        _clear_riddle(context)
        await update.message.reply_text(_riddles.correct_reply())
        if random.random() < 0.5:
            await _send_riddle(update, context, uid)
        return True

    if result == "skip":
        _clear_riddle(context)
        await update.message.reply_text("Bỏ qua à? Não lười. Câu mới:")
        await _send_riddle(update, context, uid)
        return True

    streak = context.user_data.get("cai_streak", 0) + 1
    context.user_data["cai_streak"] = streak
    await update.message.reply_text(_riddles.wrong_reply(uid, riddle))
    new_riddle = _riddles.pick(uid)
    context.user_data["active_riddle"] = new_riddle
    await update.message.reply_text(
        _riddles.intro_after_wrong() + "\n" + _riddles.format_question(new_riddle)
    )
    return True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if is_facebook_url(text):
        await _handle_facebook_link(update, text)
        return

    uid = update.effective_user.id if update.effective_user else 0

    if context.user_data.get("active_riddle"):
        if await _handle_riddle_answer(update, context, text, uid):
            return

    cai_mode = context.user_data.get("cai_mode", False)

    if cai_mode or is_trash_talk(text) or text.lower() in {
        "chui", "chửi", "cãi", "cai", "đánh nhau", "danh nhau"
    }:
        streak = context.user_data.get("cai_streak", 0) + 1
        context.user_data["cai_streak"] = streak
        await update.message.reply_text(
            generate_reply_with_streak(text, uid, streak, cai_mode=cai_mode or True)
        )
        if should_ask_riddle(streak, bool(context.user_data.get("active_riddle"))):
            await _send_riddle(update, context, uid)
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
