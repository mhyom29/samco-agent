"""
SAMCO Superstore — Telegram sales agent (long polling).

Can run two ways:

1. Standalone:      python telegram_bot.py
2. Bundled:         imported and run as a background thread by main.py,
                     alongside the website and the Paystack webhook —
                     this is what happens when you run `uvicorn main:app`.

Either way it's the same long-polling loop: no webhook, no public URL
needed just to hold a conversation. Only the Paystack payment-confirmation
webhook needs a public URL, and only if you want the automatic "payment
received!" message (checkout works fully without it either way).
"""

import time
import logging

import config
import db
import agent
import telegram

logger = logging.getLogger("samco-telegram-bot")


def handle_message(chat_id: str, text: str):
    try:
        reply = agent.run_agent_turn(chat_id, text, channel="telegram")
    except Exception:
        logger.exception("Agent failed for chat %s", chat_id)
        reply = (
            "Sorry, something went wrong on our end. A staff member will "
            "follow up with you shortly."
        )
    try:
        telegram.send_message(chat_id, reply)
    except Exception:
        logger.exception("Failed to send Telegram reply to %s", chat_id)


def run_polling():
    """Blocking long-poll loop. Call this in a background thread if you
    want it running alongside the FastAPI app; call it directly if running
    telegram_bot.py standalone."""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot will not start.")
        return

    me = telegram.get_me()
    logger.info("Logged in as @%s — SAMCO Telegram bot is live.", me["result"]["username"])

    offset = None
    while True:
        try:
            updates = telegram.get_updates(offset=offset, timeout=30)
        except Exception:
            logger.exception("Failed to fetch updates, retrying in 5s")
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message or "text" not in message:
                continue

            chat_id = str(message["chat"]["id"])
            text = message["text"]
            sender = message.get("from", {}).get("username", chat_id)
            logger.info("Message from @%s: %s", sender, text)

            handle_message(chat_id, text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db.init_db()
    run_polling()
