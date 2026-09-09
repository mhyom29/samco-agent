import requests

from config import TELEGRAM_BOT_TOKEN

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: str, text: str):
    """Sends a plain-text message to a Telegram chat."""
    resp = requests.post(
        f"{API_BASE}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_updates(offset=None, timeout=30):
    """
    Long-polls Telegram for new messages. Blocks up to `timeout` seconds
    server-side, returning immediately if a message arrives sooner — this is
    what lets the bot run without a public URL/webhook.
    """
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset

    resp = requests.get(
        f"{API_BASE}/getUpdates",
        params=params,
        timeout=timeout + 10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates error: {data}")
    return data["result"]


def get_me():
    """Quick sanity check that the bot token is valid — used by the startup log."""
    resp = requests.get(f"{API_BASE}/getMe", timeout=10)
    resp.raise_for_status()
    return resp.json()
