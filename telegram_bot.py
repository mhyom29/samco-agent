"""
Telegram long-polling fallback.

Your main.py currently uses webhook mode (/webhook/telegram) instead of this
— the polling thread that used to call run_polling() is commented out there.
This file is kept because main.py still imports it at the top level; deleting
it would break that import even though the function itself isn't called.

Useful if you ever want to switch back to polling (e.g. for local testing
without exposing a public URL): call telegram.delete_webhook() once, then
run this file directly.
"""

import time
import logging

import config
import db
import agent
import telegram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("samco-telegram-bot")


def handle_message(chat_id: str, text: str):
    try:
        reply = agent.run_agent_turn(chat_id, text, channel="telegram")
    except Exception:
        logger.exception("Agent failed for chat %s", chat_id)
        reply = "Sorry, something went wrong on our end. A staff member will follow up with you shortly."
    try:
        telegram.send_message(chat_id, reply)
    except Exception:
        logger.exception("Failed to send Telegram reply to %s", chat_id)


def run_polling():
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")

    db.init_db()
    me = telegram.get_me()
    logger.info("Logged in as @%s — SAMCO Telegram bot is live (polling mode).", me["result"]["username"])

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
    run_polling()
