import asyncio
import logging
import os
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import cai_command, chui_command, handle_message, start_command, stop_command
from bot.health import start_health_server


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    if not TELEGRAM_BOT_TOKEN:
        print("Thiếu TELEGRAM_BOT_TOKEN. Copy .env.example thành .env và điền token.")
        sys.exit(1)

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
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if os.getenv("RENDER") or os.getenv("PORT"):
        start_health_server()
        logging.info("Health server on PORT=%s", os.getenv("PORT", "10000"))

    print("Bot is running... (Ctrl+C to stop)")
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
