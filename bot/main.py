import asyncio
import logging
import os
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import (
    cai_command,
    chui_command,
    do_command,
    handle_message,
    start_command,
    stop_command,
)
from bot.health import start_health_server

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("bot.main")


def main() -> None:
    log.info("=== Bot starting ===")
    log.info("PORT=%s RENDER=%s", os.getenv("PORT"), os.getenv("RENDER"))

    if not TELEGRAM_BOT_TOKEN:
        log.error("Missing TELEGRAM_BOT_TOKEN in environment variables")
        sys.exit(1)

    log.info("Token OK (length=%d)", len(TELEGRAM_BOT_TOKEN))

    port = os.getenv("PORT")
    if port:
        start_health_server()
        log.info("Health server listening on 0.0.0.0:%s", port)

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("chui", chui_command))
    app.add_handler(CommandHandler("cai", cai_command))
    app.add_handler(CommandHandler("do", do_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Starting Telegram polling...")
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
