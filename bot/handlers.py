import logging
import re

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.lottery import (
    HELP_TEXT,
    LotteryError,
    check_numbers,
    format_results,
    parse_bet_text,
)

logger = logging.getLogger(__name__)

# "dò 39 bd 15/05/2026" | "bd 15/05/2026" | "kq bd 15/05/2026"
_TEXT_KQ = re.compile(
    r"^(?:kq|xs|xem)\s+(.+)$",
    re.IGNORECASE,
)
_TEXT_DO = re.compile(
    r"^(?:dò|do|dove|dò vé)\s+(.+)$",
    re.IGNORECASE,
)
# chỉ tỉnh + ngày: "bd 15/05/2026"
_TEXT_PROVINCE_DATE = re.compile(
    r"^([a-zA-ZÀ-ỹ\s]+?)\s+(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})\s*$",
    re.IGNORECASE,
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


async def kq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xem KQXS theo tỉnh + ngày: /kq bd 15/05/2026"""
    args = " ".join(context.args) if context.args else ""
    await _show_results(update, args)


async def dove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dò vé: /dove 39 bd 15/05/2026"""
    args = " ".join(context.args) if context.args else ""
    await _check_ticket(update, args)


async def _show_results(update: Update, text: str) -> None:
    _, region, date, province = parse_bet_text(text)
    if not province or not date:
        await update.message.reply_text(
            "Gửi tỉnh và ngày.\n\n"
            "VD: /kq binh duong 15/05/2026\n"
            "VD: /kq bd 15/05/2026"
        )
        return
    try:
        await update.message.reply_chat_action(ChatAction.TYPING)
        await update.message.reply_text(
            format_results(region, date=date, province=province)
        )
    except LotteryError as exc:
        await update.message.reply_text(str(exc))


async def _check_ticket(update: Update, text: str) -> None:
    nums, region, date, province = parse_bet_text(text)
    if not nums:
        await update.message.reply_text(
            "Gửi số + tỉnh + ngày.\n\n"
            "VD: /dove 39 bd 15/05/2026\n"
            "VD: /dove 94 660519 binh duong 15/05/2026"
        )
        return
    if not province or not date:
        await update.message.reply_text(
            "Thiếu tỉnh hoặc ngày.\n\n"
            "VD: /dove 39 bd 15/05/2026"
        )
        return
    try:
        await update.message.reply_chat_action(ChatAction.TYPING)
        await update.message.reply_text(
            check_numbers(nums, region, date=date, province=province)
        )
    except LotteryError as exc:
        await update.message.reply_text(str(exc))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    m = _TEXT_DO.match(text)
    if m:
        await _check_ticket(update, m.group(1))
        return

    m = _TEXT_KQ.match(text)
    if m:
        await _show_results(update, m.group(1))
        return

    m = _TEXT_PROVINCE_DATE.match(text)
    if m:
        await _show_results(update, f"{m.group(1)} {m.group(2)}")
        return

    # có số + tỉnh/ngày rải rác
    nums, _, date, province = parse_bet_text(text)
    if nums and province and date:
        await _check_ticket(update, text)
        return
    if province and date:
        await _show_results(update, text)
        return

    await update.message.reply_text(HELP_TEXT)
