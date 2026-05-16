import asyncio
import logging
import os
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import dove_command, handle_message, kq_command, start_command
from bot.health import start_health_server

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("bot.main")


async def _post_init(application: Application) -> None:
    me = await application.bot.get_me()
    log.info("Telegram ready: @%s (id=%s)", me.username, me.id)


def main() -> None:
    log.info("=== Lottery bot starting ===")
    log.info("PORT=%s RENDER=%s", os.getenv("PORT"), os.getenv("RENDER"))

    if not TELEGRAM_BOT_TOKEN:
        log.error("Missing TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    if os.getenv("PORT"):
        start_health_server()
        log.info("Health server on PORT=%s", os.getenv("PORT"))

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("kq", kq_command))
    app.add_handler(CommandHandler("dove", dove_command))
    app.add_handler(CommandHandler("do", dove_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Polling...")
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Bot crashed")
        sys.exit(1)
